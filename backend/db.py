import os
import logging
import uuid
from datetime import datetime, timedelta, date
from typing import Any, Dict, Optional, List, Iterable
from supabase import create_client, Client
from postgrest.exceptions import APIError

_processed_payments: set[str] = set()


_supabase: Client | None = None
logger = logging.getLogger(__name__)


DEFAULT_RETRY_PRICE = {"currency": "JPY", "amount_minor": 0, "product": "retry"}
DEFAULT_PRO_PRICE = {"currency": "JPY", "amount_minor": 0, "product": "pro_pass"}


def get_supabase() -> Client:
    """Return a cached Supabase client."""
    global _supabase
    if _supabase is None:
        supabase_url = os.environ["SUPABASE_URL"]
        supabase_api_key = os.environ["SUPABASE_API_KEY"]
        _supabase = create_client(supabase_url, supabase_api_key)
    return _supabase


def get_user(hashed_id: str) -> Optional[Dict[str, Any]]:
    """Return the user record for the given hash or ``None`` if missing."""
    supabase = get_supabase()
    resp = (
        supabase.from_("app_users")
        .select("*")
        .eq("hashed_id", hashed_id)
        .limit(1)
        .execute()
    )
    data = resp.data or []
    return data[0] if data else None


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    resp = supabase.from_("app_users").insert(user_data).execute()
    return resp.data[0]


def upsert_user(user_id: str) -> None:
    """Ensure a user row exists for ``user_id``.

    Inserts a new record if the given ``id`` is missing. Existing rows are left
    untouched.
    """

    supabase = get_supabase()
    res = (
        supabase.table("app_users").select("id").eq("id", user_id).limit(1).execute()
    )
    if res.data:
        return
    supabase.table("app_users").insert({"id": user_id}).execute()


def get_or_create_user_id_from_hashed(supabase: Client, hashed_id: str) -> str:
    """Return ``app_users.id`` (UUID) for a hashed identifier.

    If the user does not yet exist a new record is inserted and the generated
    ``id`` is returned.  Always returns a UUID string.
    """

    # Attempt to fetch an existing ID first.
    r = (
        supabase.table("app_users")
        .select("id")
        .eq("hashed_id", hashed_id)
        .limit(1)
        .execute()
    )
    if r.data:
        return r.data[0]["id"]

    # Insert a new record and try to obtain the generated ID.  Some drivers
    # require an explicit select afterwards if ``returning"` isn't enabled.
    ins = supabase.table("app_users").insert({"hashed_id": hashed_id}).execute()
    if ins.data and "id" in ins.data[0]:
        return ins.data[0]["id"]

    r2 = (
        supabase.table("app_users")
        .select("id")
        .eq("hashed_id", hashed_id)
        .limit(1)
        .execute()
    )
    return r2.data[0]["id"]


def update_user(hashed_id: str, update_data: Dict[str, Any]) -> None:
    """Update a user record with the allowed fields.

    Unknown keys or ``None`` values are stripped from ``update_data`` before
    sending the update to Supabase. The ``app_users`` table must include a
    ``demographic_completed`` column if that field is provided.
    """

    supabase = get_supabase()
    allowed_fields = {
        "plays",
        "points",
        "scores",
        "party_log",
        "referrals",
        "demographic",
        "demographic_completed",
        "free_attempts",
        "nationality",
        "survey_completed",
    }
    data_to_update = {
        k: v for k, v in update_data.items() if v is not None and k in allowed_fields
    }
    if data_to_update:
        supabase.from_("app_users").update(data_to_update).eq("hashed_id", hashed_id).execute()


def increment_free_attempts(user_id: str, delta: int = 1) -> None:
    """Increase a user's ``free_attempts`` by ``delta``."""

    supabase = get_supabase()
    current = (get_user(user_id) or {}).get("free_attempts") or 0
    supabase.table("users").update({"free_attempts": current + delta}).eq(
        "hashed_id", user_id
    ).execute()


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
    _processed_payments.add(payment_id)


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
    supabase = get_supabase()
    query = supabase.from_("surveys").select("*")
    if lang:
        query = query.eq("lang", lang)
    resp = query.execute()
    return resp.data or []


def insert_surveys(rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").insert(rows).execute()


def update_survey(group_id: str, lang: str, data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").update(data).eq("group_id", group_id).eq("lang", lang).execute()


def delete_survey(group_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").delete().eq("group_id", group_id).execute()


def insert_survey_responses(rows: List[Dict[str, Any]]) -> None:
    """Insert full survey responses for each survey item.

    Each row should contain ``user_id``, ``survey_id``, ``survey_group_id`` and
    ``answer``.
    """
    if not rows:
        return
    supabase = get_supabase()
    supabase.from_("survey_responses").insert(rows).execute()


def count_daily_survey_responses(user_id: str, answered_on: str) -> int:
    """Return how many survey items a user has answered on a given day."""
    supabase = get_supabase()
    resp = (
        supabase.table("survey_responses")
        .select("id")
        .eq("user_id", user_id)
        .eq("answered_on", answered_on)
        .execute()
    )
    return len(resp.data or [])


def get_daily_survey_response(
    user_id: str, item_id: str, answered_on: str
) -> Optional[Dict[str, Any]]:
    """Fetch an existing response for the given user/item/date if present."""
    supabase = get_supabase()
    resp = (
        supabase.table("survey_responses")
        .select("*")
        .eq("user_id", user_id)
        .eq("item_id", item_id)
        .eq("answered_on", answered_on)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def get_answered_survey_ids(user_id: str) -> List[str]:
    """Return survey_group_ids already answered by the user."""
    supabase = get_supabase()
    resp = (
        supabase.from_("survey_responses")
        .select("survey_group_id")
        .eq("user_id", user_id)
        .execute()
    )
    data = resp.data or []
    return [str(row["survey_group_id"]) for row in data if row.get("survey_group_id") is not None]


def get_survey_answers(group_id: str) -> List[Dict[str, Any]]:
    """Return option selections for a survey group.

    Previously answers were stored in a dedicated ``survey_answers`` table.
    The application now records all responses in ``survey_responses``. This
    helper derives the same structure expected by the statistics code by
    expanding each selection into ``{user_id, option_index}`` rows.
    """
    supabase = get_supabase()
    resp = (
        supabase.from_("survey_responses")
        .select("user_id, answer")
        .eq("survey_group_id", group_id)
        .execute()
    )
    rows = resp.data or []
    answers: List[Dict[str, Any]] = []
    for row in rows:
        selections = (row.get("answer") or {}).get("selections") or []
        for sel in selections:
            answers.append({"user_id": row.get("user_id"), "option_index": sel})
    return answers


def get_daily_answer_count(user_id: str, day: date) -> int:
    """Return how many poll answers a user submitted on ``day`` (UTC)."""

    supabase = get_supabase()
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    resp = (
        supabase.table("survey_responses")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", start.isoformat() + "Z")
        .lt("created_at", end.isoformat() + "Z")
        .execute()
    )
    if getattr(resp, "count", None) is not None:
        return resp.count
    return len(resp.data or [])


def insert_daily_answer(
    user_id: str, question_id: str, answer: Dict[str, Any] | None = None
) -> None:
    """Insert a single poll answer for ``user_id``."""

    supabase = get_supabase()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "survey_group_id": question_id,
        "answer": answer or {},
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    supabase.table("survey_responses").insert(row).execute()


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
