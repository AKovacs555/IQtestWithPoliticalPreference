from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db import get_supabase
import math

router = APIRouter(prefix="/stats", tags=["stats"])


class SurveyOptionAvg(BaseModel):
    option_index: int
    option_text: str
    count: int
    avg_iq: float | None


class SurveyStatsResponse(BaseModel):
    survey_id: str
    survey_title: str
    items: list[SurveyOptionAvg]


@router.get("/surveys/{survey_id}/iq_by_option", response_model=SurveyStatsResponse)
def survey_iq_by_option(survey_id: str):
    supabase = get_supabase()
    sres = (
        supabase.table("surveys")
        .select("id,title")
        .eq("id", survey_id)
        .limit(1)
        .execute()
    )
    if not sres.data:
        raise HTTPException(404, "survey_not_found")
    survey = sres.data[0]

    best_rows = (
        supabase.table("user_best_iq")
        .select("user_id,best_iq")
        .execute()
        .data
        or []
    )
    best_map: dict[str, float] = {}
    for row in best_rows:
        uid = row.get("user_id")
        sc = row.get("best_iq")
        try:
            scf = float(sc)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(scf):
            continue
        best_map[uid] = scf

    items = (
        supabase.table("survey_items")
        .select("id,position,body")
        .eq("survey_id", survey_id)
        .order("position")
        .execute()
        .data
    )
    id_to_pos = {it["id"]: it["position"] for it in items}
    idx_to_text = {it["position"]: it["body"] for it in items}

    ans = (
        supabase.table("survey_answers")
        .select("user_id,survey_item_id")
        .eq("survey_id", survey_id)
        .execute()
        .data
        or []
    )

    buckets: dict[int, list[float]] = {}
    for a in ans:
        uid = a.get("user_id")
        item_id = a.get("survey_item_id")
        idx = id_to_pos.get(item_id)
        if idx is None or uid not in best_map:
            continue
        buckets.setdefault(idx, []).append(best_map[uid])

    resp_items: list[SurveyOptionAvg] = []
    for idx, text in idx_to_text.items():
        values = buckets.get(idx, [])
        avg = round(sum(values) / len(values), 2) if values else None
        resp_items.append(
            SurveyOptionAvg(
                option_index=idx,
                option_text=text,
                count=len(values),
                avg_iq=avg,
            )
        )

    return SurveyStatsResponse(
        survey_id=survey["id"],
        survey_title=survey["title"],
        items=resp_items,
    )


@router.get("/surveys/with_data")
def surveys_with_any_answers():
    supabase = get_supabase()
    try:
        q = supabase.rpc("surveys_with_any_answers").execute()
        return q.data
    except Exception:
        rows = (
            supabase.table("survey_answers")
            .select("survey_id")
            .execute()
            .data
            or []
        )
        seen: set[str] = set()
        result = []
        for r in rows:
            sid = r.get("survey_id")
            if sid and sid not in seen:
                seen.add(sid)
                result.append({"id": sid})
        return result
