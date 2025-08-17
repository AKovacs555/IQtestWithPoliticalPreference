import os
import logging
import uuid
from datetime import datetime, date
from typing import Any, Dict, Optional, List, Iterable
import random
from supabase import create_client, Client
from postgrest.exceptions import APIError

_processed_payments: set[str] = set()


_supabase: Client | None = None
logger = logging.getLogger(__name__)

ALLOWED_USER_UPDATE_FIELDS = {
    "nationality",
    "demographic",
    "username",
    "survey_completed",
    "is_admin",
    "points",
    "plays",
    "referrals",
    "party_log",
    "scores",
    "invite_code",
    "referred_by",
}

DEFAULT_RETRY_PRICE = {"currency": "JPY", "amount_minor": 0, "product": "retry"}
DEFAULT_PRO_PRICE = {"currency": "JPY", "amount_minor": 0, "product": "pro_pass"}


def get_supabase() -> Client:
    """Return a cached Supabase client."""

    global _supabase
    if _supabase is not None:
        if not (
            os.environ.get("SUPABASE_API_KEY")
            or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
        ):
            # Environment no longer configured; drop cached client.
            _supabase = None
        else:
            return _supabase

    supabase_url = os.environ.get("SUPABASE_URL", "http://localhost")
    supabase_api_key = (
        os.environ.get("SUPABASE_API_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
    )
    if not supabase_api_key:
        raise KeyError("SUPABASE_API_KEY")
    _supabase = create_client(supabase_url, supabase_api_key)
    return _supabase


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Return the user record for the given id or hashed_id.

    Supabase JWTs encode the user's UUID in the ``sub`` claim, so we first
    attempt to resolve the row by ``id``.  For backwards compatibility with
    older tokens that supplied a ``hashed_id`` we fall back to that column if no
    match is found.
    """

    supabase = get_supabase()
    # Primary lookup by id for Supabase-authenticated users
    resp = (
        supabase.from_("app_users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    data = resp.data or []
    if data:
        return data[0]

    # Fallback to hashed_id for legacy callers
    resp = (
        supabase.from_("app_users")
        .select("*")
        .eq("hashed_id", user_id)
        .execute()
    )
    data = resp.data or []
    if data:
        return data[0]

    # Legacy support: some tests insert into a ``users`` table.
    resp = (
        supabase.from_("users")
        .select("*")
        .eq("hashed_id", user_id)
        .execute()
    )
    data = resp.data or []
    if data:
        return data[0]

    resp = (
        supabase.from_("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    data = resp.data or []
    return data[0] if data else None


def _generate_invite_code() -> str:
    """Return a short random invite code."""

    return "".join(
        random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)
    )


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new user row with sensible defaults."""

    supabase = get_supabase()
    base = {
        "survey_completed": False,
        "is_admin": False,
        "points": 0,
        "plays": 0,
        "referrals": 0,
        "party_log": [],
        "scores": [],
    }
    if "invite_code" not in user_data:
        base["invite_code"] = _generate_invite_code()
    data = {**base, **user_data}
    data.pop("salt", None)
    resp = supabase.from_("app_users").insert(data).execute()
    row = resp.data[0]
    return row


def upsert_user(user_id: str, username: str | None = None) -> None:
    """Ensure a user row exists for ``user_id``.

    Inserts a new record if the given ``id`` is missing. Existing rows are left
    untouched. When ``username`` is provided it is stored or updated.
    """

    supabase = get_supabase()
    res = supabase.table("app_users").select("id").eq("id", user_id).execute()
    if res.data:
        if username:
            update_user(supabase, user_id, {"username": username})
        return
    payload = {
        "id": user_id,
        "hashed_id": user_id,
        "points": 0,
        "plays": 0,
        "referrals": 0,
        "party_log": [],
        "scores": [],
        "invite_code": _generate_invite_code(),
    }
    if username is not None:
        payload["username"] = username
    supabase.table("app_users").upsert(payload).execute()


def get_or_create_user_id_from_hashed(
    supabase: Client, hashed_id: str
) -> str | None:
    """Return ``app_users.id`` for a hashed identifier.

    If the user does not exist a new record is created with ``id`` and
    ``hashed_id`` set to ``hashed_id`` and ``username`` defaulting to the same
    value. Returns the resulting
    ``id`` or ``None`` on failure.
    """

    # Look up an existing user first.
    res = (
        supabase.table("app_users")
        .select("id")
        .eq("hashed_id", hashed_id)
        .execute()
    )
    data = res.data or []
    if data:
        return data[0]["id"]

    # Create the user when missing.
    supabase.table("app_users").upsert(
        {"id": hashed_id, "hashed_id": hashed_id, "username": hashed_id}
    ).execute()

    res = (
        supabase.table("app_users")
        .select("id")
        .eq("hashed_id", hashed_id)
        .execute()
    )
    data = res.data or []
    return data[0]["id"] if data else None


def update_user(supabase: Client, hashed_id: str, data_to_update: Dict[str, Any]) -> None:
    """Update a single ``app_users`` row with a safe payload."""

    if not data_to_update:
        return

    payload = {k: v for k, v in data_to_update.items() if k in ALLOWED_USER_UPDATE_FIELDS}
    if not payload:
        return
    try:
        supabase.table("app_users").update(payload).eq("hashed_id", hashed_id).execute()
    except APIError as exc:  # ignore unknown column errors for backwards compatibility
        code = getattr(exc, "code", "")
        msg = str(exc).lower()
        if code in ("PGRST204", "42703") or (
            "column" in msg and "does not exist" in msg
        ):
            logger.warning("Ignored unknown column(s) on app_users: %s", payload.keys())
            return
        raise


# The legacy attempt ledger and free attempt functions have been removed in
# favor of a points-based system handled entirely via database updates.


# ---------------------------------------------------------------------------
# Points helpers
# ---------------------------------------------------------------------------

def get_points(user_id: str) -> int:
    """Return the current points balance for ``user_id``.

    Missing users or ``points`` columns are treated as zero so the function is
    safe to call in legacy environments.
    """

    supabase = get_supabase()
    try:
        resp = (
            supabase.table("app_users")
            .select("points")
            .eq("id", user_id)
            .single()
            .execute()
        )
        pts = (resp.data or {}).get("points", 0)
        return int(pts) if isinstance(pts, (int, float)) else 0
    except APIError as exc:  # pragma: no cover - missing column
        code = getattr(exc, "code", "")
        if code in ("PGRST204", "42703"):
            return 0
        raise




def record_payment_event(
    payment_id: str,
    user_id: Optional[str],
    status: Optional[str],
    amount: Optional[float],
    currency: Optional[str],
    raw: Dict[str, Any],
) -> bool:
    """Persist a payment notification to the ``payments`` table.

    Returns ``True`` if the event was recorded, ``False`` if a record with the
    same ``payment_id`` already exists.
    """

    supabase = get_supabase()
    data = {
        "payment_id": payment_id,
        "user_id": user_id,
        "status": status,
        "amount": amount,
        "currency": currency,
        "raw": raw,
    }
    try:
        supabase.table("payments").insert(data).execute()
        return True
    except APIError as exc:  # pragma: no cover - network error
        # ``23505`` is the Postgres unique violation code
        if getattr(exc, "code", "") == "23505" or "duplicate" in str(exc).lower():
            return False
        raise


def get_all_users() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.from_("app_users").select("*").execute()
    return resp.data or []


def is_payment_processed(payment_id: str) -> bool:
    """Return ``True`` if ``payment_id`` has already been handled.

    The current implementation keeps the set in memory only.  TODO: persist to
    Supabase for durability and cross-process safety.
    """

    return payment_id in _processed_payments


def mark_payment_processed(payment_id: str) -> None:
    """Mark ``payment_id`` as processed by setting ``processed_at``."""

    supabase = get_supabase()
    supabase.table("payments").update({"processed_at": datetime.utcnow().isoformat()}).eq(
        "payment_id", payment_id
    ).execute()


# ---------------------------------------------------------------------------
# RPC wrappers for points
# ---------------------------------------------------------------------------

from backend.core.supabase_admin import supabase_admin


def spend_point(user_id: str | uuid.UUID, reason: str, meta: dict | None = None) -> bool:
    """Attempt to atomically spend a single point.

    Returns ``True`` on success, ``False`` when the user has insufficient
    balance.
    """

    payload = {"user_id": str(user_id), "reason": reason, "meta": meta or {}}
    resp = supabase_admin.rpc("spend_point", payload).execute()
    return bool(resp.data)


def credit_points(
    user_id: str | uuid.UUID, delta: int, reason: str, meta: dict | None = None
) -> None:
    """Credit ``delta`` points to ``user_id`` via RPC."""

    payload = {
        "user_id": str(user_id),
        "delta": delta,
        "reason": reason,
        "meta": meta or {},
    }
    supabase_admin.rpc("credit_points", payload).execute()


def credit_points_once_per_day(
    user_id: str | uuid.UUID, delta: int, reason: str, meta: dict | None = None
) -> bool:
    """Credit points only if the user has not already received them today."""

    payload = {
        "user_id": str(user_id),
        "delta": delta,
        "reason": reason,
        "meta": meta or {},
    }
    resp = supabase_admin.rpc("credit_points_once_per_day", payload).execute()
    return bool(resp.data)


# ---------------------------------------------------------------------------
# Question helpers
# ---------------------------------------------------------------------------


def get_questions(lang: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = (
        supabase.from_("questions").select("*").eq("lang", lang).execute()
    )
    return resp.data or []


def insert_questions(rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.from_("questions").insert(rows).execute()


def update_question(question_id: str, data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("questions").update(data).eq("id", question_id).execute()


def delete_question(question_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("questions").delete().eq("id", question_id).execute()


def get_group_key_by_id(qid: str) -> Optional[str]:
    """Return orig_id or group_id for the given question ``id``."""
    supabase = get_supabase()
    try:
        res = (
            supabase.table("questions")
            .select("orig_id, group_id")
            .eq("id", qid)
            .single()
            .execute()
        )
    except Exception as e:  # pragma: no cover - logging only
        logger.error("Error fetching group key for %s: %s", qid, getattr(e, "message", e))
        raise
    row = res.data or {}
    return row.get("orig_id") or row.get("group_id")


def update_question_group(
    group_key: str, values: Dict, text_fields: Iterable[str], apply_text_to_all: bool
) -> None:
    """Update all rows within the same group."""
    supabase = get_supabase()
    payload = dict(values)
    if not apply_text_to_all:
        for f in text_fields:
            payload.pop(f, None)
    try:
        (
            supabase.table("questions")
            .update(payload)
            .eq("orig_id", group_key)
            .execute()
        )
    except Exception as e:  # pragma: no cover - logging only
        logger.error(
            "Error updating question group %s: %s", group_key, getattr(e, "message", e)
        )
        raise


def approve_question_group(group_key: str, approved: bool) -> None:
    supabase = get_supabase()
    try:
        (
            supabase.table("questions")
            .update({"approved": approved})
            .eq("orig_id", group_key)
            .execute()
        )
    except Exception as e:  # pragma: no cover - logging only
        logger.error(
            "Error approving question group %s: %s", group_key, getattr(e, "message", e)
        )
        raise


def delete_question_group(group_key: str) -> None:
    supabase = get_supabase()
    try:
        supabase.table("questions").delete().eq("orig_id", group_key).execute()
    except Exception as e:  # pragma: no cover - logging only
        logger.error(
            "Error deleting question group %s: %s", group_key, getattr(e, "message", e)
        )
        raise


# ---------------------------------------------------------------------------
# Survey helpers
# ---------------------------------------------------------------------------


def get_surveys(lang: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return surveys with their choice items.

    Only surveys matching ``lang`` are returned when provided.  Choice items are
    ordered by ``position`` so the caller can render them directly.  ``options``
    and ``exclusive_options`` are derived for convenience.
    """

    supabase = get_supabase()
    select = (
        "id,title,question_text,lang,target_countries,target_genders,type,status,group_id," "survey_items(id,position,body,is_exclusive)"
    )
    query = supabase.from_("surveys").select(select)
    if lang:
        query = query.eq("lang", lang)
    resp = query.execute()
    surveys = resp.data or []
    for s in surveys:
        items = s.get("survey_items") or []
        items.sort(key=lambda it: it.get("position", 0))
        s["options"] = [
            (it.get("body") or it.get("label") or it.get("text") or it.get("statement") or "")
            for it in items
        ]
        s["exclusive_options"] = [
            idx for idx, it in enumerate(items) if it.get("is_exclusive")
        ]
    return surveys


def insert_surveys(rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").insert(rows).execute()


def update_survey(group_id: str, lang: str, data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").update(data).eq("group_id", group_id).eq("lang", lang).execute()


def delete_survey(group_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").delete().eq("group_id", group_id).execute()


def insert_survey_answers(rows: List[Dict[str, Any]]) -> None:
    """Insert survey answers for each selected option into ``survey_answers``."""

    if not rows:
        return
    supabase = get_supabase()
    answer_rows: List[Dict[str, Any]] = []
    for r in rows:
        ans = r.get("answer") or {}
        for sel in ans.get("selections") or []:
            answer_rows.append(
                {
                    "user_id": r.get("user_id"),
                    "survey_id": r.get("survey_id"),
                    "survey_group_id": r.get("survey_group_id"),
                    "survey_item_id": f"{ans.get('id')}-{sel}",
                }
            )
    if answer_rows:
        supabase.from_("survey_answers").insert(answer_rows).execute()


def get_daily_survey_response(
    user_id: str, item_id: str, answered_on: str
) -> Optional[Dict[str, Any]]:
    """Fetch an existing response for the given user/item/date if present."""
    supabase = get_supabase()
    resp = (
        supabase.table("survey_answers")
        .select("*")
        .eq("user_id", user_id)
        .eq("survey_item_id", item_id)
        .eq("answered_on", answered_on)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def get_answered_survey_group_ids(user_id: str) -> List[str]:
    """Return survey ``group_id`` values already answered by the user."""

    supabase = get_supabase()
    resp = (
        supabase.from_("survey_answers")
        .select("survey_group_id")
        .eq("user_id", user_id)
        .execute()
    )
    data = resp.data or []
    return list(
        {
            str(row["survey_group_id"])
            for row in data
            if row.get("survey_group_id") is not None
        }
    )


def get_survey_answers(group_id: str) -> List[Dict[str, Any]]:
    """Return option selections for a survey group using ``survey_answers``."""

    supabase = get_supabase()
    resp = (
        supabase.from_("survey_answers")
        .select("user_id,survey_id,survey_item_id")
        .eq("survey_group_id", group_id)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return []
    # Map item IDs to their option index
    surveys = get_surveys()
    id_to_idx: Dict[str, int] = {}
    for s in surveys:
        for idx, it in enumerate(s.get("survey_items") or []):
            id_to_idx[it.get("id")] = idx
    answers: List[Dict[str, Any]] = []
    for row in rows:
        idx = id_to_idx.get(row.get("survey_item_id"))
        if idx is None:
            continue
        answers.append({"user_id": row.get("user_id"), "option_index": idx})
    return answers


def get_daily_answer_count(hashed_id: str, target_date: date) -> int:
    """Return the number of survey answers submitted on ``target_date``."""

    supabase = get_supabase()
    resp = (
        supabase.table("survey_answers")
        .select("id")
        .eq("user_id", hashed_id)
        .eq("answered_on", target_date.isoformat())
        .execute()
    )
    rows = resp.data or []
    return len(rows)


def insert_daily_answer(
    user_id: str, question_id: str, answer: Dict[str, Any] | None = None
) -> None:
    """Insert a single poll answer for ``user_id``."""

    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "survey_group_id": question_id,
        "survey_id": question_id,
        "survey_item_id": question_id,
        "answer": answer or {},
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    supabase.table("survey_answers").insert(row).execute()


def get_dashboard_default_survey() -> Optional[str]:
    supabase = get_supabase()
    resp = (
        supabase.from_("dashboard_settings")
        .select("default_survey_group_id")
        .limit(1)
        .execute()
    )
    data = resp.data or []
    return data[0]["default_survey_group_id"] if data else None


def set_dashboard_default_survey(group_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("dashboard_settings").upsert(
        {"id": 1, "default_survey_group_id": group_id}
    ).execute()


def get_parties() -> List[Dict[str, Any]]:
    """Return a list of parties.

    Deprecated: the parties feature has been disabled and this function now
    returns an empty list.
    """

    # Parties feature disabled; return empty list
    return []


def insert_parties(rows: List[Dict[str, Any]]) -> None:
    """Insert political parties into the database.

    Deprecated: the parties feature has been disabled and this function now
    performs no operation.
    """

    # Parties feature disabled; do nothing
    return

# ---------------------------------------------------------------------------
# Pricing rules
# ---------------------------------------------------------------------------

def list_pricing_rules() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.from_("pricing_rules").select("*").execute()
    return resp.data or []

def get_pricing_rule(country: str, product: str):
    supabase = get_supabase()
    try:
        res = (
            supabase.table("pricing_rules")
            .select("*")
            .eq("country", country)
            .eq("product", product)
            .eq("active", True)
            .limit(1)
            .execute()
        )
        items = getattr(res, "data", None) or []
        return items[0] if items else None
    except APIError as e:
        msg = getattr(e, "message", str(e))
        code = getattr(e, "code", None)
        if (code == "42P01") or ("does not exist" in msg.lower()) or ("not found" in msg.lower()):
            logger.warning("pricing_rules missing; fallback pricing used")
            return None
        raise

def upsert_pricing_rule(data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    resp = supabase.from_("pricing_rules").upsert(data).execute()
    return resp.data[0]

def delete_pricing_rule(rule_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("pricing_rules").delete().eq("id", rule_id).execute()


def log_event(user_hid: str, name: str, meta: dict | None = None):
    supabase = get_supabase()
    row = {"user_hid": user_hid, "name": name, "metadata": meta or None}
    try:
        supabase.table("events").insert(row).execute()
    except APIError as e:
        msg = getattr(e, "message", str(e))
        code = getattr(e, "code", None)
        if (code == "42P01") or ("does not exist" in msg.lower()) or ("not found" in msg.lower()):
            logger.warning("events table missing; skipping event insert")
            return
        logger.exception("failed to insert event")
