"""Arena analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend import db

router = APIRouter(prefix="/arena", tags=["arena"])


@router.get("/iq_stats")
def iq_stats(scope: str = "group", group_id: str | None = None, survey_id: str | None = None):
    """Return IQ statistics for survey answers."""

    supabase = db.get_supabase()
    if scope == "group":
        q = supabase.table("survey_group_choice_iq_stats").select("*")
        if group_id:
            q = q.eq("group_id", group_id)
        if survey_id:
            q = q.eq("survey_id", survey_id)
        return q.execute().data or []
    if scope == "item":
        q = supabase.table("survey_choice_iq_stats").select("*")
        if survey_id:
            q = q.eq("survey_id", survey_id)
        if group_id:
            q = q.eq("group_id", group_id)
        return q.execute().data or []
    if scope == "survey":
        q = supabase.table("survey_choice_iq_stats").select("*")
        if survey_id:
            q = q.eq("survey_id", survey_id)
        if group_id:
            q = q.eq("group_id", group_id)
        rows = q.execute().data or []
        agg: dict[str, dict] = {}
        for r in rows:
            sid = r.get("survey_id")
            entry = agg.setdefault(
                sid,
                {
                    "survey_id": sid,
                    "group_id": r.get("group_id"),
                    "responses_count": 0,
                    "avg_iq": 0.0,
                },
            )
            cnt = r.get("responses_count") or 0
            avg = r.get("avg_iq") or 0
            entry["responses_count"] += cnt
            entry["avg_iq"] += avg * cnt
        for val in agg.values():
            if val["responses_count"]:
                val["avg_iq"] /= val["responses_count"]
        return list(agg.values())
    raise HTTPException(400, "invalid scope")
