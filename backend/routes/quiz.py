import os
import secrets
import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
import random
from pydantic import BaseModel
from backend.deps.supabase_client import get_supabase_client
from backend.questions import available_sets, get_balanced_random_questions_by_set
from backend.scoring import estimate_theta, iq_score, ability_summary, standard_error
from backend.irt import percentile
from backend.features import generate_share_image
from backend.deps.auth import get_current_user
from backend.db import get_answered_survey_ids, insert_survey_responses

router = APIRouter(prefix="/quiz", tags=["quiz"])

NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))

_dist_path = Path(__file__).resolve().parents[1] / "data" / "normative_distribution.json"
with _dist_path.open() as f:
    NORMATIVE_DIST = json.load(f)

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    image: str | None = None

class QuizStartResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]
    pending_surveys: Optional[List[dict]] = None

class QuizAnswer(BaseModel):
    id: int
    answer: int

class SurveyAnswer(BaseModel):
    survey_group_id: str
    answer: dict


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: List[QuizAnswer]
    surveys: Optional[List[SurveyAnswer]] = None

@router.get("/sets")
async def quiz_sets():
    return {"sets": available_sets()}

@router.get("/start", response_model=QuizStartResponse)
async def start_quiz(
    request: Request,
    set_id: str | None = None,
    lang: str = "ja",
    user: dict = Depends(get_current_user),
):
    if user and not user.get("nationality"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "nationality_required",
                "message": "Please select your nationality before taking the IQ test.",
            },
        )
    if user and not user.get("survey_completed"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "survey_required",
                "message": "Please complete the survey before taking the IQ test.",
            },
        )
    if set_id:
        try:
            questions = get_balanced_random_questions_by_set(NUM_QUESTIONS, set_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        supabase = get_supabase_client()
        easy = int(round(NUM_QUESTIONS * 0.3))
        med = int(round(NUM_QUESTIONS * 0.4))
        hard = NUM_QUESTIONS - easy - med

        if lang:
            def fetch_subset(lower, upper, limit):
                query = (
                    supabase.table("questions")
                    .select("*")
                    .eq("lang", lang)
                    .eq("approved", True)
                )
                if lower is not None:
                    query = query.gte("irt_b", lower)
                if upper is not None:
                    query = query.lt("irt_b", upper)
                # Fetch all matching questions and randomize on the client side
                rows = query.execute().data or []
                random.shuffle(rows)
                unique = []
                seen = set()
                for r in rows:
                    gid = r.get("group_id")
                    if gid in seen:
                        continue
                    seen.add(gid)
                    unique.append(r)
                    if len(unique) == limit:
                        break
                if len(unique) < limit:
                    for r in rows:
                        if len(unique) == limit:
                            break
                        if r not in unique:
                            unique.append(r)
                if len(unique) < limit:
                    logging.getLogger(__name__).warning(
                        "fetch_subset returned %d questions but %d requested",
                        len(unique),
                        limit,
                    )
                return unique

            easy_qs = fetch_subset(None, -0.33, easy)
            med_qs = fetch_subset(-0.33, 0.33, med)
            hard_qs = fetch_subset(0.33, None, hard)
            questions = easy_qs + med_qs + hard_qs
            random.shuffle(questions)
        else:
            resp = supabase.rpc(
                "fetch_exam",
                {"_easy": easy, "_med": med, "_hard": hard},
            ).execute()
            if resp.error:
                raise HTTPException(status_code=500, detail=resp.error.message)
            questions = [q for q in resp.data if q.get("approved")]
    session_id = secrets.token_hex(8)
    request.app.state.sessions[session_id] = {
        q["id"]: {"answer": q["answer"], "a": q.get("irt_a"), "b": q.get("irt_b")}
        for q in questions
    }
    models = []
    for q in questions:
        models.append(
            QuizQuestion(
                id=q["id"],
                question=q["question"],
                options=q["options"],
                image=q.get("image"),
            )
        )
    pending = get_random_pending_surveys(
        user["hashed_id"], user.get("nationality"), limit=3
    )
    return {"session_id": session_id, "questions": models, "pending_surveys": pending}

@router.post("/submit")
async def submit_quiz(
    payload: QuizSubmitRequest, request: Request, user: dict = Depends(get_current_user)
):
    session = request.app.state.sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    if len(payload.answers) != len(session):
        raise HTTPException(status_code=400, detail="Expected all answers")
    responses = []
    for item in payload.answers:
        info = session.get(item.id)
        if not info:
            continue
        correct = item.answer == info["answer"]
        responses.append({"a": info.get("a", 1.0), "b": info.get("b", 0.0), "correct": correct})
    theta = estimate_theta(responses)
    iq = iq_score(theta)
    pct = percentile(theta, NORMATIVE_DIST)
    ability = ability_summary(theta)
    se = standard_error(theta, responses)
    share_url = generate_share_image(user["hashed_id"], iq, pct)
    supabase = get_supabase_client()
    supabase.table("user_scores").insert(
        {
            "user_id": user["hashed_id"],
            "session_id": payload.session_id,
            "iq": iq,
            "percentile": pct,
        }
    ).execute()

    if payload.surveys:
        rows = [
            {
                "user_id": user["hashed_id"],
                "survey_id": s.answer.get("id"),
                "survey_group_id": s.survey_group_id,
                "answer": s.answer,
            }
            for s in payload.surveys
        ]
        insert_survey_responses(rows)

    if user.get("referrer_id"):
        try:
            ref_id = user["referrer_id"]
            limit_resp = (
                supabase.table("settings")
                .select("invitation_reward_limit")
                .limit(1)
                .execute()
            )
            limit = (
                (limit_resp.data or [{}])[0].get("invitation_reward_limit")
                or int(os.getenv("INVITATION_REWARD_LIMIT", "0"))
            )
            count_resp = (
                supabase.table("invitation_rewards")
                .select("id")
                .eq("referrer_id", ref_id)
                .execute()
            )
            count = len(count_resp.data or [])
            if count < int(limit):
                supabase.table("users").update({"free_tests": "free_tests + 1"}).eq(
                    "hashed_id", ref_id
                ).execute()
                supabase.table("invitation_rewards").insert(
                    {"referrer_id": ref_id, "referred_id": user["hashed_id"]}
                ).execute()
        except Exception:
            pass
    request.app.state.sessions.pop(payload.session_id, None)
    return {
        "theta": theta,
        "iq": iq,
        "percentile": pct,
        "ability": ability,
        "se": se,
        "share_url": share_url,
    }


def get_random_pending_surveys(
    user_id: str, nationality: Optional[str], limit: int = 3
) -> List[dict]:
    """Return up to ``limit`` approved surveys the user hasn't answered."""
    try:
        supabase = get_supabase_client()
        answered = set(get_answered_survey_ids(user_id))
        resp = supabase.table("surveys").select("*").eq("approved", True).execute()
    except Exception:
        return []
    surveys = resp.data or []
    eligible: List[dict] = []
    for s in surveys:
        countries = s.get("target_countries") or []
        if countries and nationality not in countries:
            continue
        if str(s.get("group_id")) in answered:
            continue
        eligible.append(s)
    random.shuffle(eligible)
    return eligible[:limit]
