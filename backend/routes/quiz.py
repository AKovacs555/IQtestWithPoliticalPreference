import os
import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import RedirectResponse
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
    get_daily_answer_count,
    spend_points,
)
from backend.utils.settings import get_setting_int, get_setting_bool
from backend.schemas.quiz import (
    AttemptStartResponse,
    AttemptQuestionsResponse,
    QuestionDTO,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)

NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))
# Default quiz duration: 5 minutes unless overridden via env var
QUIZ_DURATION_MINUTES = int(os.getenv("QUIZ_DURATION_MINUTES", "5"))

_dist_path = Path(__file__).resolve().parents[1] / "data" / "normative_distribution.json"
with _dist_path.open() as f:
    NORMATIVE_DIST = json.load(f)


def _generate_set_id(length: int = 12) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(alphabet) for _ in range(length))

class QuizAnswer(BaseModel):
    id: str | int
    answer: int

class SurveyAnswer(BaseModel):
    survey_group_id: str
    answer: dict


class QuizSubmitRequest(BaseModel):
    attempt_id: str
    answers: List[QuizAnswer]
    surveys: Optional[List[SurveyAnswer]] = None


class QuizAbandonRequest(BaseModel):
    attempt_id: str

@router.get("/sets")
async def quiz_sets():
    return {"sets": get_question_sets()}

@router.get("/start", response_model=AttemptStartResponse)
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
    # Validate static set_id if provided
    if set_id:
        try:
            get_question_sets()  # ensure sets loaded
            get_balanced_random_questions_by_set(1, set_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    supabase = get_supabase_client()
    daily_count = get_daily_answer_count(user["hashed_id"])
    points = int(user.get("points", 0))
    cost = get_setting_int(supabase, "attempt_cost_points", 1)
    if points < cost and daily_count < 3:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "survey_required",
                "message": "Please complete the survey before taking the IQ test.",
            },
        )
    # Determine subscription status (no point deduction yet)
    pro_active = False
    pro_until = user.get("pro_active_until")
    if pro_until:
        try:
            pro_dt = datetime.fromisoformat(str(pro_until).replace("Z", ""))
            pro_active = pro_dt > datetime.now(timezone.utc)
        except ValueError:
            pro_active = False

    logger.info("quiz_start_allowed")
    if set_id:
        try:
            questions = get_balanced_random_questions_by_set(NUM_QUESTIONS, set_id, lang)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        easy_count = int(round(NUM_QUESTIONS * 0.3))
        med_count = int(round(NUM_QUESTIONS * 0.4))
        hard_count = NUM_QUESTIONS - easy_count - med_count

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
            easy_qs = fetch_subset(None, -0.33, easy_count, seen_groups)
            med_qs = fetch_subset(-0.33, 0.33, med_count, seen_groups)
            hard_qs = fetch_subset(0.33, None, hard_count, seen_groups)
            questions = easy_qs + med_qs + hard_qs
            if len(questions) < NUM_QUESTIONS:
                questions += fetch_subset(None, None, NUM_QUESTIONS - len(questions), seen_groups)
            random.shuffle(questions)
        else:
            resp = supabase.rpc(
                "fetch_exam",
                {"_easy": easy_count, "_med": med_count, "_hard": hard_count},
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

    question_ids = [q["id"] for q in questions]
    set_id = set_id or _generate_set_id()
    supabase = get_supabase_client()
    try:
        supabase.table("question_sets").insert({
            "id": set_id,
            "question_ids": question_ids,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        # If insertion fails (e.g., duplicate set_id), ignore and proceed
        pass

    attempt_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=QUIZ_DURATION_MINUTES or 10)
    request.app.state.sessions[attempt_id] = {
        str(q["id"]): {"answer": q["answer"], "a": q.get("irt_a"), "b": q.get("irt_b")}
        for q in questions
    }
    if not hasattr(request.app.state, "session_expires"):
        request.app.state.session_expires = {}
    if not hasattr(request.app.state, "session_started"):
        request.app.state.session_started = {}
    request.app.state.session_expires[attempt_id] = expires_at
    request.app.state.session_started[attempt_id] = datetime.now(timezone.utc)
    try:
        supabase.table("quiz_attempts").insert(
            {
                "id": attempt_id,
                "user_id": user.get("hashed_id"),
                "set_id": set_id,
                "status": "started",
            }
        ).execute()
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not create session record: %s", e)

    return {"attempt_id": attempt_id, "set_id": set_id}


@router.get("/attempts/{attempt_id}/questions", response_model=AttemptQuestionsResponse)
async def attempt_questions(attempt_id: str, user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    attempt = (
        supabase.table("quiz_attempts")
        .select("set_id")
        .eq("id", attempt_id)
        .single()
        .execute()
    )
    if not attempt.data:
        raise HTTPException(status_code=404, detail={"code": "attempt_not_found", "message": "Attempt not found"})
    set_id = attempt.data.get("set_id")
    qs = (
        supabase.table("question_sets")
        .select("question_ids")
        .eq("id", set_id)
        .single()
        .execute()
    )
    question_ids: List[int] = qs.data.get("question_ids") if qs.data else []
    if not question_ids:
        raise HTTPException(status_code=404, detail={"code": "questions_not_found", "message": "Questions not found"})
    rows = (
        supabase.table("questions")
        .select("id, question, options, option_images, irt_a, irt_b, image, lang")
        .in_("id", question_ids)
        .execute()
        .data
        or []
    )
    if not rows:
        raise HTTPException(status_code=404, detail={"code": "questions_not_found", "message": "Questions not found"})
    by_id = {r["id"]: r for r in rows}
    items = [QuestionDTO(**by_id[qid]) for qid in question_ids if qid in by_id]
    return {"attempt_id": attempt_id, "set_id": set_id, "items": items}

@router.post("/submit")
async def submit_quiz(
    payload: QuizSubmitRequest, request: Request, user: dict = Depends(get_current_user)
):
    supabase = get_supabase_client()
    session = request.app.state.sessions.get(payload.attempt_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    expires_at = getattr(request.app.state, "session_expires", {}).get(payload.attempt_id)
    if not expires_at:
        request.app.state.sessions.pop(payload.attempt_id, None)
        raise HTTPException(status_code=400, detail="Invalid session")

    # Consume points at submission time for non-pro users
    pro_active = False
    pro_until = user.get("pro_active_until")
    if pro_until:
        try:
            pro_dt = datetime.fromisoformat(str(pro_until).replace("Z", ""))
            pro_active = pro_dt > datetime.now(timezone.utc)
        except ValueError:
            pro_active = False
    if not pro_active:
        cost = get_setting_int(supabase, "attempt_cost_points", 1)
        remaining = spend_points(user["hashed_id"], cost)
        if remaining is None:
            logger.error("points_insufficient", extra={"user_id": user["hashed_id"]})
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "insufficient_points",
                    "message": "ポイントが不足しています。",
                },
            )
        logger.info(
            "points_consume_ok", extra={"user_id": user["hashed_id"], "remaining": remaining}
        )

    # If time is up, mark as timeout but still proceed to score answered questions
    expired = False
    if datetime.now(timezone.utc) > expires_at:
        expired = True
        logger.info("quiz_timeout", extra={"attempt_id": payload.attempt_id})

    # Do NOT require all answers – unanswered questions count as incorrect
    answers_map = {str(item.id): item.answer for item in payload.answers}
    responses = []
    for qid, info in session.items():
        ans = answers_map.get(str(qid))
        correct = ans == info["answer"]
        responses.append({"a": info.get("a", 1.0), "b": info.get("b", 0.0), "correct": correct})
    theta = estimate_theta(responses)
    iq = iq_score(theta)
    pct = percentile(theta, NORMATIVE_DIST)
    ability = ability_summary(theta)
    se = standard_error(theta, responses)
    share_url = generate_share_image(user["hashed_id"], iq, pct)
    try:
        supabase.from_("user_scores").insert(
            {
                "user_id": user["hashed_id"],
                "session_id": payload.attempt_id,
                "iq": iq,
                "percentile": pct,
            }
        ).execute()
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not store user score: %s", e)
    start_time = getattr(request.app.state, "session_started", {}).get(payload.attempt_id)
    duration = None
    if start_time:
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds())
    try:
        update_data = {
            "status": "timeout" if expired else "submitted",
            "iq_score": iq,
            "percentile": pct,
        }
        if duration is not None:
            update_data["duration"] = duration
        supabase.table("quiz_attempts").update(update_data).eq(
            "id", payload.attempt_id
        ).execute()
    except Exception:  # pragma: no cover - best effort only
        pass
    try:
        scores = (user.get("scores") or []) + [
            {
                "iq": iq,
                "percentile": pct,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
        plays = (user.get("plays") or 0) + 1
        update_user(supabase, user["hashed_id"], {"scores": scores, "plays": plays})
    except Exception as e:  # pragma: no cover - best effort only
        logging.getLogger(__name__).warning("Could not update user record: %s", e)

    try:
        best = (
            supabase.table("user_best_iq_unified")
            .select("best_iq")
            .eq("user_id", user["hashed_id"])
            .single()
            .execute()
            .data
        )
        current = None
        if best and best.get("best_iq") is not None:
            try:
                current = float(best["best_iq"])
            except (TypeError, ValueError):
                current = None
        if current is None:
            supabase.table("user_best_iq").insert(
                {"user_id": user["hashed_id"], "best_iq": iq}
            ).execute()
        elif iq > current:
            supabase.table("user_best_iq").update({"best_iq": iq}).eq(
                "user_id", user["hashed_id"]
            ).execute()
    except Exception:  # pragma: no cover - best effort only
        pass

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

        await credit_referral_if_applicable(user["hashed_id"])
    except Exception:
        pass
    request.app.state.sessions.pop(payload.attempt_id, None)
    getattr(request.app.state, "session_expires", {}).pop(payload.attempt_id, None)
    getattr(request.app.state, "session_started", {}).pop(payload.attempt_id, None)
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
        supabase.table("quiz_attempts").update({"status": "abandoned"}).eq(
            "id", payload.attempt_id
        ).eq("status", "started").execute()
    except Exception:
        pass
    request.app.state.sessions.pop(payload.attempt_id, None)
    getattr(request.app.state, "session_expires", {}).pop(payload.attempt_id, None)
    getattr(request.app.state, "session_started", {}).pop(payload.attempt_id, None)
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


@router.post("/answer")
async def cat_answer():  # pragma: no cover - skeleton
    supabase = get_supabase_client()
    if not get_setting_bool(supabase, "cat_enabled", False):
        raise HTTPException(status_code=503, detail={"code": "cat_disabled", "message": "CAT disabled"})
    raise HTTPException(status_code=501, detail={"code": "not_implemented", "message": "CAT answer not implemented"})


@router.get("/next")
async def cat_next():  # pragma: no cover - skeleton
    supabase = get_supabase_client()
    if not get_setting_bool(supabase, "cat_enabled", False):
        raise HTTPException(status_code=503, detail={"code": "cat_disabled", "message": "CAT disabled"})
    raise HTTPException(status_code=501, detail={"code": "not_implemented", "message": "CAT next not implemented"})


@router.post("/finish")
async def cat_finish():  # pragma: no cover - skeleton
    supabase = get_supabase_client()
    if not get_setting_bool(supabase, "cat_enabled", False):
        raise HTTPException(status_code=503, detail={"code": "cat_disabled", "message": "CAT disabled"})
    raise HTTPException(status_code=501, detail={"code": "not_implemented", "message": "CAT finish not implemented"})
