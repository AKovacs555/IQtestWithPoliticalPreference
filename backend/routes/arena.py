"""Arena analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.services import db_read

router = APIRouter(prefix="/arena", tags=["arena"])


@router.get("/iq_stats")
def iq_stats(scope: str = "group", group_id: str | None = None, survey_id: str | None = None):
    """Return IQ statistics for survey answers."""

    if scope == "group":
        rows = db_read.get_survey_group_choice_iq_stats(group_id=group_id, survey_id=survey_id)
        payload = [r.model_dump() for r in rows]
        return JSONResponse(payload, headers=db_read.cache_headers(payload))
    if scope == "item":
        rows = db_read.get_survey_choice_iq_stats(survey_id=survey_id, group_id=group_id)
        payload = [r.model_dump() for r in rows]
        return JSONResponse(payload, headers=db_read.cache_headers(payload))
    if scope == "survey":
        rows = db_read.get_survey_choice_iq_stats(survey_id=survey_id, group_id=group_id)
        agg: dict[str, dict] = {}
        for r in rows:
            sid = r.survey_id
            entry = agg.setdefault(
                sid,
                {
                    "survey_id": sid,
                    "group_id": r.group_id,
                    "responses_count": 0,
                    "avg_iq": 0.0,
                },
            )
            cnt = r.responses_count or 0
            avg = r.avg_iq or 0
            entry["responses_count"] += cnt
            entry["avg_iq"] += avg * cnt
        for val in agg.values():
            if val["responses_count"]:
                val["avg_iq"] /= val["responses_count"]
        result = list(agg.values())
        return JSONResponse(result, headers=db_read.cache_headers(result))
    raise HTTPException(400, "invalid scope")
