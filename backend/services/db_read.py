import os
import json
import hashlib
from fastapi.encoders import jsonable_encoder
from typing import List, Optional

from pydantic import BaseModel

from backend import db


def _use_v2() -> bool:
    return os.getenv("USE_V2_STATS", "false").lower() in {"1", "true", "yes"}

class UserBestIQ(BaseModel):
    user_id: str
    best_iq: float


class SurveyChoiceIQStat(BaseModel):
    group_id: Optional[str]
    survey_id: str
    survey_item_id: Optional[str]
    responses_count: int
    avg_iq: Optional[float]


class SurveyGroupChoiceIQStat(BaseModel):
    group_id: str
    survey_id: str
    survey_item_id: Optional[str]
    responses_count: int
    avg_iq: Optional[float]


def _table(name: str) -> str:
    if _use_v2():
        return f"{name}_v2"
    return name


def get_user_best_iq(user_id: str) -> Optional[UserBestIQ]:
    """Return a user's best IQ score."""

    supabase = db.get_supabase()
    view = _table("user_best_iq_unified")
    row = db.with_retries(
        lambda: supabase.table(view)
        .select("user_id,best_iq")
        .eq("user_id", user_id)
        .single()
        .execute()
        .data
    )
    if not row:
        return None
    try:
        return UserBestIQ(user_id=row["user_id"], best_iq=float(row["best_iq"]))
    except (KeyError, TypeError, ValueError):
        return None


def get_survey_choice_iq_stats(survey_id: str | None = None, group_id: str | None = None) -> List[SurveyChoiceIQStat]:
    """Return IQ stats for each survey item."""

    supabase = db.get_supabase()
    view = _table("survey_choice_iq_stats")
    q = supabase.table(view).select("group_id,survey_id,survey_item_id,responses_count,avg_iq")
    if survey_id:
        q = q.eq("survey_id", survey_id)
    if group_id:
        q = q.eq("group_id", group_id)
    rows = db.with_retries(lambda: q.execute().data or [])
    return [SurveyChoiceIQStat(**r) for r in rows]


def get_survey_group_choice_iq_stats(group_id: str | None = None, survey_id: str | None = None) -> List[SurveyGroupChoiceIQStat]:
    """Return IQ stats aggregated by survey group."""

    supabase = db.get_supabase()
    view = _table("survey_group_choice_iq_stats")
    q = supabase.table(view).select("group_id,survey_id,survey_item_id,responses_count,avg_iq")
    if group_id:
        q = q.eq("group_id", group_id)
    if survey_id:
        q = q.eq("survey_id", survey_id)
    rows = db.with_retries(lambda: q.execute().data or [])
    return [SurveyGroupChoiceIQStat(**r) for r in rows]


def cache_headers(payload: object) -> dict:
    """Return caching headers and an ETag for ``payload``."""

    body = json.dumps(jsonable_encoder(payload), sort_keys=True, separators=(",", ":")).encode()
    etag = hashlib.sha256(body).hexdigest()
    return {
        "Cache-Control": "public, max-age=60, stale-while-revalidate=300",
        "ETag": etag,
    }
