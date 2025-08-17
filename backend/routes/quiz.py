import os
import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
import random
from pydantic import BaseModel
from backend.deps.supabase_client import get_supabase_client
from backend.db import update_user
from backend.questions_loader import (
    get_question_sets,
    get_questions_for_set,
)
# Backwards compatibility for tests
def get_balanced_random_questions_by_set(n: int, set_id: str, lang: str | None = None):
    return get_questions_for_set(set_id, n, lang)

from backend.questions import get_balanced_random_questions_global  # noqa: E402

from backend.scoring import estimate_theta, iq_score, ability_summary, standard_error  # noqa: E402
from backend.irt import percentile  # noqa: E402
from backend.features import generate_share_image  # noqa: E402
from backend.deps.auth import get_current_user  # noqa: E402
from backend.db import (  # noqa: E402
    get_answered_survey_group_ids,
    insert_survey_answers,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)

NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))
QUIZ_DURATION_MINUTES = int(os.getenv("QUIZ_DURATION_MINUTES", "25"))

_dist_path = Path(__file__).resolve().parents[1] / "data" / "normative_distribution.json"
with _dist_path.open() as f:
    NORMATIVE_DIST = json.load(f)

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    image: str | None = None
    option_images: List[str] | None = None

class QuizStartResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]
    pending_surveys: Optional[List[dict]] = None

class QuizAnswer(BaseModel):
    id: str | int
    answer: int

class SurveyAnswer(BaseModel):
    survey_group_id: str
    answer: dict


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: List[QuizAnswer]
    surveys: Optional[List[SurveyAnswer]] = None


class QuizAbandonRequest(BaseModel):
    session_id: str

@router.get("/sets")
async def quiz_sets():
    return {"sets": get_question_sets()}

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
    if user and not (user.get("demographic") or user.get("demographic_completed")):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "demographic_required",
                "message": "Please complete the demographics form before taking the IQ test.",
            },
        )
    supabase = get_supabase_client()
    if set_id:
        try:
            get_balanced_random_questions_by_set(1, set_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    pending_surveys = get_random_pending_surveys(
        user["hashed_id"], user.get("nationality"), user.get("gender"), lang=lang, limit=3
    )
    is_pro = bool(
        user.get("pro_active_until")
        and datetime.now(timezone.utc)
        < datetime.fromisoformat(user["pro_active_until"])
    )
    if not is_pro:
        ok = supabase.rpc(
            "spend_points", {"p_user_id": str(user["id"]), "p_cost": 1}
        ).execute().data
        if not ok:
            logger.error("points_insufficient", extra={"user_id": user["id"]})
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "points_insufficient",
                    "message": "ポイントが不足しています。",
                },
            )
    logger.info("quiz_start_allowed")
    if set_id:
        try:
            questions = get_balanced_random_questions_by_set(NUM_QUESTIONS, set_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        supabase = get_supabase_client()
        easy = int(round(NUM_QUESTIONS * 0.3))
        med = int(round(NUM_QUESTIONS * 0.4))
        hard = NUM_QUESTIONS - easy - med

        if lang:
            def fetch_subset(lower, upper, limit, seen_groups=None):
                seen_groups = seen_groups or set()
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
                for r in rows:
                    gid = r.get("group_id")
                    if gid in seen_groups:
                        continue
                    seen_groups.add(gid)
                    unique.append(r)
                    if len(unique) == limit:
                        break
                if len(unique) < limit:
                    for r in rows:
                        if len(unique) == limit:
                            break
                        if r not in unique and r.get("group_id") not in seen_groups:
                            seen_groups.add(r.get("group_id"))
                            unique.append(r)
                if len(unique) < limit:
                    logging.getLogger(__name__).warning(
                        "fetch_subset returned %d questions but %d requested",
                        len(unique),
                        limit,
                    )
                return unique

            seen_groups: set[str] = set()
            easy_qs = fetch_subset(None, -0.33, easy, seen_groups)
            med_qs = fetch_subset(-0.33, 0.33, med, seen_groups)
            hard_qs = fetch_subset(0.33, None, hard, seen_groups)
            questions = easy_qs + med_qs + hard_qs
            if len(questions) < NUM_QUESTIONS:
                questions += fetch_subset(None, None, NUM_QUESTIONS - len(questions), seen_groups)
            random.shuffle(questions)
        else:
            resp = supabase.rpc(
                "fetch_exam",
                {"_easy": easy, "_med": med, "_hard": hard},
            ).execute()
            if resp.error:
                raise HTTPException(status_code=500, detail=resp.error.message)
            questions = [q for q in resp.data if q.get("approved")]

    if not questions:
        try:
            questions = get_balanced_random_questions_global(NUM_QUESTIONS, lang)
        except Exception:
            logging.getLogger(__name__).error("No questions available for language %s", lang)
            raise HTTPException(status_code=500, detail="No questions available")

    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=QUIZ_DURATION_MINUTES)
    request.app.state.sessions[session_id] = {
        str(q["id"]): {"answer": q["answer"], "a": q.get("irt_a"), "b": q.get("irt_b")}
        for q in questions
    }
    supabase = get_supabase_client()
    try:
        supabase.table("quiz_sessions").insert(
            {
                "id": session_id,
                "user_id": user.get("hashed_id"),
                "status": "started",
                "expires_at": expires_at.isoformat(),
                "set_id": set_id,
            }
        ).execute()
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not create session record: %s", e)
    models = []
    for q in questions:
        models.append(
            QuizQuestion(
                id=str(q["id"]),
                question=q.get("question") or q.get("prompt", ""),
                options=[str(o.get("id")) for o in q.get("options", [])] if q.get("options") and isinstance(q.get("options")[0], dict) else q.get("options", []),
                image=q.get("image"),
                option_images=[o.get("image") for o in q.get("options", [])] if q.get("options") and isinstance(q.get("options")[0], dict) else q.get("option_images"),
            )
        )
    return {
        "session_id": session_id,
        "expires_at": expires_at.isoformat(),
        "questions": models,
        "pending_surveys": pending_surveys or [],
    }

@router.post("/submit")
async def submit_quiz(
    payload: QuizSubmitRequest, request: Request, user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    row = (
        supabase.table("quiz_sessions")
        .select("status,expires_at,set_id")
        .eq("id", payload.session_id)
        .single()
        .execute()
        .data
    )
    if not row or row.get("status") != "started":
        raise HTTPException(status_code=400, detail="Invalid session")
    try:
        exp = datetime.fromisoformat(row["expires_at"])
    except Exception:
        exp = datetime.utcnow()
    if datetime.utcnow() > exp:
        try:
            supabase.table("quiz_sessions").update({"status": "timeout"}).eq(
                "id", payload.session_id
            ).execute()
        except Exception:
            pass
        request.app.state.sessions.pop(payload.session_id, None)
        raise HTTPException(status_code=400, detail="Session expired")
    session = request.app.state.sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    if len(payload.answers) != len(session):
        raise HTTPException(status_code=400, detail="Expected all answers")
    responses = []
    for item in payload.answers:
        info = session.get(str(item.id)) or (session.get(int(item.id)) if isinstance(item.id, (int, str)) and str(item.id).isdigit() else None)
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
    is_pro = bool(
        user.get("pro_active_until")
        and datetime.now(timezone.utc)
        < datetime.fromisoformat(user["pro_active_until"])
    )
    try:
        supabase.from_("user_scores").insert(
            {
                "user_id": user["hashed_id"],
                "session_id": payload.session_id,
                "iq": iq,
                "percentile": pct,
            }
        ).execute()
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not store user score: %s", e)
    try:
        supabase.table("quiz_attempts").insert(
            {
                "user_id": user["hashed_id"],
                "set_id": row.get("set_id"),
                "status": "submitted",
                "iq_score": iq,
                "percentile": pct,
                "paid": not is_pro,
            }
        ).execute()
    except Exception:  # pragma: no cover - best effort only
        pass
    try:
        scores = (user.get("scores") or []) + [
            {
                "iq": iq,
                "percentile": pct,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
        plays = (user.get("plays") or 0) + 1
        update_user(supabase, user["hashed_id"], {"scores": scores, "plays": plays})
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not update user record: %s", e)

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
        insert_survey_answers(rows)

    try:
        from backend.referral import credit_referral_if_applicable

        credit_referral_if_applicable(user["hashed_id"])
    except Exception:
        pass
    try:
        supabase.table("quiz_sessions").update(
            {"status": "submitted", "score": iq, "percentile": pct}
        ).eq("id", payload.session_id).execute()
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


@router.post("/abandon")
async def abandon_quiz(
    payload: QuizAbandonRequest, request: Request, user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    try:
        supabase.table("quiz_sessions").update({"status": "abandoned"}).eq("id", payload.session_id).eq(
            "status", "started"
        ).execute()
    except Exception:
        pass
    request.app.state.sessions.pop(payload.session_id, None)
    return {"status": "abandoned"}


def get_random_pending_surveys(
    user_id: str,
    country: Optional[str],
    gender: Optional[str],
    *,
    lang: str,
    limit: int = 3,
) -> List[dict] | None:
    """Return up to ``limit`` surveys matching the user's language, country and gender.

    Returns ``None`` if the lookup fails.
    """

    try:
        supabase = get_supabase_client()
        answered = set(get_answered_survey_group_ids(user_id))
        resp = (
            supabase.table("surveys")
            .select("*")
            .eq("lang", lang)
            .eq("status", "approved")
            .execute()
        )
    except Exception:
        return None
    surveys = resp.data or []
    eligible: List[dict] = []
    for s in surveys:
        countries = s.get("target_countries") or []
        if countries and country not in countries:
            continue
        genders = s.get("target_genders") or []
        if genders and gender not in genders:
            continue
        if str(s.get("group_id")) in answered:
            continue
        opts = (
            supabase.table("survey_items")
            .select("*")
            .eq("survey_id", s["id"])
            .eq("lang", s.get("lang"))
            .eq("is_active", True)
            .execute()
            .data
            or []
        )
        opts = sorted(opts, key=lambda o: o.get("position", 0))
        eligible.append(
            {
                "survey_id": s["id"],
                "survey_group_id": s.get("group_id"),
                "question_text": s.get("question_text"),
                "selection_type": s.get("type"),
                "options": [
                    {
                        "id": o["id"],
                        "option_text": o.get("body") or o.get("option_text"),
                        "is_exclusive": o.get("is_exclusive", False),
                        "requires_text": o.get("requires_text", False),
                        "order": o.get("position"),
                    }
                    for o in opts
                ],
            }
        )
    random.shuffle(eligible)
    return eligible[:limit]
