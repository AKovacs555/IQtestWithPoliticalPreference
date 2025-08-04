import os
import secrets
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Request
import random
from pydantic import BaseModel
from backend.deps.supabase_client import get_supabase_client
from backend.questions import available_sets, get_balanced_random_questions_by_set
from backend.scoring import estimate_theta, iq_score, ability_summary, standard_error
from backend.irt import percentile
from backend.features import generate_share_image
from backend.db import get_user

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

class QuizAnswer(BaseModel):
    id: int
    answer: int

class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: List[QuizAnswer]
    user_id: str | None = None

@router.get("/sets")
async def quiz_sets():
    return {"sets": available_sets()}

@router.get("/start", response_model=QuizStartResponse)
async def start_quiz(
    request: Request,
    set_id: str | None = None,
    lang: str = "ja",
    user_id: str | None = None,
):
    if user_id:
        user = get_user(user_id)
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
    return {"session_id": session_id, "questions": models}

@router.post("/submit")
async def submit_quiz(payload: QuizSubmitRequest, request: Request):
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
    share_url = generate_share_image(payload.user_id or "anon", iq, pct)
    request.app.state.sessions.pop(payload.session_id, None)
    return {"theta": theta, "iq": iq, "percentile": pct, "ability": ability, "se": se, "share_url": share_url}
