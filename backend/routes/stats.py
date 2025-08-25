from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db import get_supabase, with_retries
from backend.services import db_read
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/stats", tags=["stats"])


class SurveyOptionAvg(BaseModel):
    option_index: int
    option_text: str
    count: int
    avg_iq: float | None


class SurveyStatsResponse(BaseModel):
    survey_id: str
    survey_title: str
    survey_question_text: str | None = None
    items: list[SurveyOptionAvg]


@router.get("/surveys/{survey_id}/iq_by_option", response_model=SurveyStatsResponse)
def survey_iq_by_option(survey_id: str):
    supabase = get_supabase()
    sres = with_retries(
        lambda: supabase.table("surveys").select("id,title,question_text").eq("id", survey_id).limit(1).execute()
    )
    if not sres.data:
        raise HTTPException(404, "survey_not_found")
    survey = sres.data[0]
    items = with_retries(
        lambda: supabase.table("survey_items").select("id,position,body").eq("survey_id", survey_id).order("position").execute().data
    )
    rows = with_retries(
        lambda: supabase
        .table("survey_choice_iq_stats_v2")
        .select("survey_item_id,responses_count,avg_iq")
        .eq("survey_id", survey_id)
        .execute()
        .data
        or []
    )
    if not rows:
        best_rows = (
            supabase.table("m_user_best_iq")
            .select("user_id,best_iq")
            .execute()
            .data
            or []
        )
        if not best_rows:
            best_rows = (
                supabase.table("user_best_iq_unified")
                .select("user_id,best_iq")
                .execute()
                .data
                or []
            )
        best_map: dict[str, float] = {
            r["user_id"]: float(r["best_iq"]) for r in best_rows if r.get("user_id") and r.get("best_iq") is not None
        }
        ans = (
            supabase.table("survey_answers")
            .select("user_id,survey_item_id")
            .eq("survey_id", survey_id)
            .execute()
            .data
            or []
        )
        buckets: dict[str, list[float]] = {}
        for a in ans:
            uid = a.get("user_id")
            item_id = a.get("survey_item_id")
            if uid in best_map and item_id:
                buckets.setdefault(item_id, []).append(best_map[uid])
        rows = [
            {"survey_item_id": k, "responses_count": len(v), "avg_iq": (sum(v) / len(v) if v else None)}
            for k, v in buckets.items()
        ]
    stat_map = {r["survey_item_id"]: r for r in rows}
    resp_items: list[SurveyOptionAvg] = []
    for it in items:
        s = stat_map.get(it['id'])
        resp_items.append(
            SurveyOptionAvg(
                option_index=it['position'],
                option_text=it['body'],
                count=s["responses_count"] if s else 0,
                avg_iq=s["avg_iq"] if s else None,
            )
        )
    payload = SurveyStatsResponse(
        survey_id=survey['id'],
        survey_title=survey['title'],
        survey_question_text=survey.get('question_text'),
        items=resp_items,
    )
    data = payload.model_dump()
    return JSONResponse(data, headers=db_read.cache_headers(data))

@router.get("/surveys/with_data")
def surveys_with_any_answers():
    supabase = get_supabase()
    try:
        q = with_retries(lambda: supabase.rpc("surveys_with_any_answers").execute())
        return q.data
    except Exception:
        rows = with_retries(
            lambda: (
                supabase.table("survey_answers")
                .select("survey_id")
                .execute()
                .data
                or []
            )
        )
        seen: set[str] = set()
        result = []
        for r in rows:
            sid = r.get("survey_id")
            if sid and sid not in seen:
                seen.add(sid)
                result.append({"id": sid})
        return result
