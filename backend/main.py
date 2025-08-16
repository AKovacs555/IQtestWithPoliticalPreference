"""FastAPI backend application."""

# ruff: noqa: E402

import os
import hashlib
import hmac
import secrets
from typing import List, Optional

import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the backend package and repository root are on the Python path
backend_dir = os.path.dirname(__file__)
repo_root = os.path.join(backend_dir, "..")
sys.path.extend([backend_dir, repo_root])

from fastapi import FastAPI, HTTPException, Depends, Request, APIRouter
from fastapi.responses import JSONResponse
import io
import contextlib
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
from tools.generate_questions import import_dir

from backend.routes.dependencies import require_admin
from features import (
    generate_share_image,
    update_normative_distribution,
    dp_average,
    MIN_BUCKET_SIZE,
)
from demographics import collect_demographics

from questions import (
    QUESTION_MAP,
    get_random_questions,
)
from adaptive import select_next_question, should_stop
from irt import update_theta, percentile
from scoring import (
    estimate_theta,
    iq_score,
    ability_summary,
    standard_error,
)
from payment import (
    select_processor,
    create_nowpayments_invoice,
)
from analytics import log_event as track_event
from tools.dif_analysis import dif_report
from routes.exam import router as exam_router
from routes.admin_questions import router as admin_questions_router
from routes.admin_import_questions import router as admin_import_router
from routes.admin_surveys import router as admin_surveys_router
from routes.admin_users import router as admin_users_router
from routes.admin_pricing import router as admin_pricing_router
from routes.settings import router as settings_router
from routes.quiz import router as quiz_router
from routes.daily import router as daily_router
from routes.surveys import router as surveys_router
from routes.survey_start import router as survey_start_router
from routes.user import router as user_router
from routes.sms import router as sms_router
from routes.referral import router as referral_router
from routes.custom_survey import (
    router as custom_survey_router,
    admin_router as custom_survey_admin_router,
)
from routes.leaderboard import router as leaderboard_router
from routes.nowpayments import router as nowpayments_router
from routes.points import router as points_router
from routes.arena import router as arena_router
from backend.routes import user_profile_bootstrap
from api import diagnostics
import json
from utils.settings import get_setting

app = FastAPI()
app.state.sessions = {}
app.state.otps = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://i-qtest-with-political-preference.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exam_router)

# Admin routers
app.include_router(admin_questions_router)
app.include_router(admin_import_router)
app.include_router(admin_surveys_router)
app.include_router(admin_users_router)
app.include_router(admin_pricing_router)
app.include_router(settings_router)
app.include_router(diagnostics.router)

# Public routers
app.include_router(quiz_router)
app.include_router(daily_router)
app.include_router(surveys_router)
app.include_router(survey_start_router)
app.include_router(user_router)
app.include_router(leaderboard_router)
app.include_router(sms_router)
app.include_router(nowpayments_router)
app.include_router(referral_router)
app.include_router(points_router)
app.include_router(arena_router)
app.include_router(
    user_profile_bootstrap.router, prefix="/user", tags=["user"]
)
app.include_router(custom_survey_router)
app.include_router(custom_survey_admin_router)

# SMS provider handled by sms_service module

# Number of questions per quiz session
NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))


from db import (
    get_user,
    create_user as db_create_user,
    update_user as db_update_user,
    get_all_users,
    get_supabase,
    get_surveys,
    get_survey_answers,
    get_answered_survey_group_ids,
    insert_survey_answers,
    get_pricing_rule,
    get_or_create_user_id_from_hashed,
    upsert_user,
    log_event,
    DEFAULT_RETRY_PRICE,
    DEFAULT_PRO_PRICE,
    increment_free_attempts,
    mark_payment_processed,
    is_payment_processed,
)
from postgrest.exceptions import APIError
from backend.core.supabase_admin import supabase_admin
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_API_KEY is not configured")

EVENTS: list[dict] = []


router = APIRouter()


def detect_country(request: Request) -> str:
    return (
        request.headers.get("cf-country")
        or request.headers.get("cf_country")
        or request.headers.get("x-country")
        or "JP"
    ).upper()


class UpsertUserIn(BaseModel):
    user_id: str
    username: str | None = None


@router.post("/auth/upsert_user")
def upsert_user_api(payload: UpsertUserIn):
    upsert_user(payload.user_id, payload.username)
    return {"ok": True}


app.include_router(router)

# Dynamic pricing tiers loaded from RETRY_PRICE_TIERS
def _load_price_tiers() -> list[int]:
    tiers = os.getenv("RETRY_PRICE_TIERS", "480,720,980")
    try:
        values = [int(t.strip()) for t in tiers.split(",") if t.strip()]
    except ValueError:
        values = [480, 720, 980]
    return [0] + values

PRICES = _load_price_tiers()
PRO_PRICE_MONTHLY = int(os.getenv("PRO_PRICE_MONTHLY", "980"))

PRICE_VARIANTS = [480, 720, 980]

# Reward ad configuration
AD_REWARD_POINTS = int(os.getenv("AD_REWARD_POINTS", "1"))
RETRY_POINT_COST = int(os.getenv("RETRY_POINT_COST", "5"))

# Load normative distribution for percentile scores
_dist_path = os.path.join(
    os.path.dirname(__file__), "data", "normative_distribution.json"
)
with open(_dist_path) as f:
    NORMATIVE_DIST = json.load(f)


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    image: Optional[str] = None
    option_images: Optional[List[str]] = None


class QuizStartResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]


class QuizAnswer(BaseModel):
    id: int
    answer: int


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class AdaptiveStartResponse(BaseModel):
    session_id: str
    question: QuizQuestion


class AdaptiveAnswerRequest(BaseModel):
    session_id: str
    answer: int


class AdaptiveAnswerResponse(BaseModel):
    finished: bool
    next_question: Optional[QuizQuestion] = None
    score: Optional[float] = None
    percentile: Optional[float] = None


from uuid import UUID


class SurveyInfo(BaseModel):
    id: UUID
    group_id: UUID
    lang: str
    title: str | None = None
    question_text: str | None = None
    is_single_choice: bool | None = False


class SurveyItem(BaseModel):
    id: UUID
    body: str
    is_exclusive: bool | None = False
    position: int
    lang: str | None = None


class SurveyStartResponse(BaseModel):
    survey: SurveyInfo
    items: List[SurveyItem]


class Answer(BaseModel):
    id: UUID
    selections: List[int] | None = None
    item_ids: List[UUID] | None = None


class SurveySubmit(BaseModel):
    user_id: UUID | None = None
    lang: str | None = None
    survey_id: UUID
    survey_group_id: UUID
    answers: List[Answer]


class DemographicInfo(BaseModel):
    user_id: str
    age_band: str
    gender: str
    income_band: str
    occupation: str

class PricingResponse(BaseModel):
    price: int
    retry_price: int
    plays: int
    free_attempts: int
    processor: str
    pro_price: int
    variant: int
    currency: str = "JPY"


class ScoreEntry(BaseModel):
    iq: float
    percentile: float
    timestamp: str | None = None
    set_id: str | None = None


class UserStats(BaseModel):
    plays: int
    referrals: int
    scores: list[ScoreEntry]
    party_log: list
    free_attempts: int


class HistoryResponse(BaseModel):
    scores: list[ScoreEntry]


class UserAction(BaseModel):
    user_id: str


class PurchaseRequest(BaseModel):
    user_id: str
    amount: int
    pay_currency: str | None = None



class QuestionUpload(BaseModel):
    questions: list


def hash_phone(phone: str, salt: str) -> str:
    return hmac.new(salt.encode(), phone.encode(), hashlib.sha256).hexdigest()


# Adaptive testing session store
OTP_CODES = {}


@app.get("/pricing/{user_hid}")
def pricing(user_hid: str, request: Request):
    try:
        country = detect_country(request)
        rule_retry = get_pricing_rule(country, "retry") or DEFAULT_RETRY_PRICE
        rule_pro = get_pricing_rule(country, "pro_pass") or DEFAULT_PRO_PRICE
        return {"country": country, "retry": rule_retry, "pro_pass": rule_pro}
    except Exception as e:  # pragma: no cover - logging only
        logger.exception("pricing endpoint fallback", exc_info=e)
        return {
            "country": "JP",
            "retry": DEFAULT_RETRY_PRICE,
            "pro_pass": DEFAULT_PRO_PRICE,
        }


@app.post("/purchase")
async def purchase(payload: PurchaseRequest, region: str = "US"):
    processor = select_processor(region)
    if processor == "nowpayments":
        invoice = create_nowpayments_invoice(
            str(payload.amount),
            os.getenv("NOWPAYMENTS_CURRENCY", "USD"),
            payload.pay_currency,
            payload.user_id,
        )
        return {
            "processor": processor,
            "payment_url": invoice.get("invoice_url") or invoice.get("payment_url"),
            "payment_id": invoice.get("payment_id"),
        }
    raise HTTPException(status_code=400, detail="Payment processor not configured")


@app.post("/payment/nowpayments/callback")
async def nowpayments_callback(request: Request):
    ipn_secret = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except Exception:  # pragma: no cover - invalid payload
        raise HTTPException(status_code=400, detail={"error": "invalid_json"})

    signature = request.headers.get("x-nowpayments-sig", "")
    sorted_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    expected = hmac.new(ipn_secret.encode(), sorted_payload.encode(), hashlib.sha512).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        logger.warning(
            "NOWP IPN invalid signature for payment_id=%s", payload.get("payment_id")
        )
        return JSONResponse(status_code=401, content={"error": "invalid_signature"})

    payment_id = str(payload.get("payment_id"))
    status = payload.get("payment_status")
    if status in {"finished", "confirmed"}:
        if is_payment_processed(payment_id):
            logger.info(
                "NOWP IPN processed already, skipping credit payment_id=%s", payment_id
            )
        else:
            user_id = payload.get("order_id") or payload.get("user_id")
            if user_id:
                increment_free_attempts(user_id, 1)
            mark_payment_processed(payment_id)
            track_event({"event": "nowpayments_finished", "payment_id": payment_id})

    return {"status": "ok"}


@app.post("/play/record")
async def record_play(action: UserAction):
    max_free_attempts = await get_setting("max_free_attempts", 1)
    user = get_user(action.user_id)
    if not user:
        user = db_create_user(
            {"hashed_id": action.user_id, "free_attempts": max_free_attempts}
        )
    paid = False
    remaining = min(user.get("free_attempts", max_free_attempts), max_free_attempts)
    if user.get("free_attempts", max_free_attempts) != remaining:
        user["free_attempts"] = remaining
    if remaining > 0:
        user["free_attempts"] = remaining - 1
    else:
        if user.get("points", 0) >= RETRY_POINT_COST:
            user["points"] -= RETRY_POINT_COST
            paid = True
        else:
            raise HTTPException(
                status_code=402,
                detail={"error": "max_free_attempts_reached", "message": "Please upgrade"},
            )
    user["plays"] = user.get("plays", 0) + 1
    supabase = get_supabase()
    db_update_user(
        supabase,
        action.user_id,
        {
            "plays": user["plays"],
            "points": user.get("points", 0),
            "free_attempts": user.get("free_attempts", 0),
        },
    )
    track_event({"event": "play_record", "user_id": action.user_id, "paid": paid})
    return {"plays": user["plays"], "points": user.get("points", 0), "free_attempts": user.get("free_attempts", 0)}


@app.post("/referral")
async def referral(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user({"id": action.user_id, "hashed_id": action.user_id})
    user["referrals"] = user.get("referrals", 0) + 1
    supabase = get_supabase()
    db_update_user(supabase, action.user_id, {"referrals": user["referrals"]})
    return {"referrals": user["referrals"]}


@app.post("/ads/start")
async def ads_start(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user({"id": action.user_id, "hashed_id": action.user_id})
    track_event({"event": "ad_start", "user_id": action.user_id})
    return {"status": "started"}


@app.post("/ads/complete")
async def ads_complete(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user({"hashed_id": action.user_id})
    user["points"] = user.get("points", 0) + AD_REWARD_POINTS
    supabase = get_supabase()
    db_update_user(supabase, action.user_id, {"points": user["points"]})
    track_event({"event": "ad_complete", "user_id": action.user_id})
    return {"points": user["points"]}


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/share-image/{user_id}")
async def share_image(user_id: str, iq: float, percentile: float):
    """Generate and return a shareable result image URL."""
    url = generate_share_image(user_id, iq, percentile)
    return {"url": url}




def _to_model(q) -> QuizQuestion:
    return QuizQuestion(
        id=q["id"],
        question=q["question"],
        options=q["options"],
        image=q.get("image"),
        option_images=q.get("option_images"),
    )


@app.get("/adaptive/start", response_model=AdaptiveStartResponse)
async def adaptive_start(set_id: str | None = None, user_id: str | None = None):
    """Begin an adaptive quiz session."""
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
    theta = 0.0
    session_id = secrets.token_hex(8)
    questions = get_random_questions(NUM_QUESTIONS, set_id)
    question = select_next_question(theta, [], questions)
    app.state.sessions[session_id] = {
        "theta": theta,
        "asked": [question["id"]],
        "answers": [],
        "pool": questions,
    }
    return {"session_id": session_id, "question": _to_model(question)}


@app.post("/adaptive/answer", response_model=AdaptiveAnswerResponse)
async def adaptive_answer(payload: AdaptiveAnswerRequest):
    session = app.state.sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    qid = session["asked"][-1]
    question = QUESTION_MAP.get(qid)
    if not question:
        raise HTTPException(status_code=400, detail="Question not found")
    correct = payload.answer == question["answer"]
    old_theta = session["theta"]
    session["theta"] = update_theta(
        old_theta, question["irt"]["a"], question["irt"]["b"], correct
    )
    session["answers"].append(
        {
            "id": qid,
            "a": question["irt"]["a"],
            "b": question["irt"]["b"],
            "correct": correct,
        }
    )

    if should_stop(session["theta"], session["answers"]):
        theta = estimate_theta(session["answers"])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        se = standard_error(theta, session["answers"])
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del app.state.sessions[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
            "se": se,
            "share_url": share_url,
        }

    next_q = select_next_question(session["theta"], session["asked"], session["pool"])
    if next_q is None:
        theta = estimate_theta(session["answers"])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        se = standard_error(theta, session["answers"])
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del app.state.sessions[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
            "se": se,
            "share_url": share_url,
        }
    session["asked"].append(next_q["id"])
    return {"finished": False, "next_question": _to_model(next_q)}


@app.get("/survey/start", response_model=SurveyStartResponse)
async def survey_start(
    lang: str = "en", user_id: str | None = None, nationality: str | None = None
):
    supabase = get_supabase()
    user = get_user(user_id) if user_id else None
    user_country = nationality or (user.get("nationality") if user else None)
    user_gender = (user.get("gender") if user else None)

    langs = [lang]
    if lang != "en":
        langs.append("en")

    try:
        q = (
            supabase.table("surveys")
            .select("*")
            .eq("is_active", True)
            .eq("status", "approved")
            .in_("lang", langs)
        )
        rows = q.execute().data or []
    except AttributeError:
        rows = (
            supabase.table("surveys").select("*").execute().data or []
        )
        rows = [
            r
            for r in rows
            if r.get("is_active")
            and r.get("status") == "approved"
            and r.get("lang") in langs
        ]

    answered_groups: set[str] = set()
    if user_id:
        answered_groups = set(get_answered_survey_group_ids(user_id))

    now = datetime.now(timezone.utc)
    candidates: list[dict] = []
    for r in rows:
        if str(r.get("group_id")) in answered_groups:
            continue
        start_date = r.get("start_date")
        if start_date:
            dt = datetime.fromisoformat(str(start_date).replace("Z", "+00:00"))
            if dt > now:
                continue
        end_date = r.get("end_date")
        if end_date:
            dt = datetime.fromisoformat(str(end_date).replace("Z", "+00:00"))
            if dt < now:
                continue
        countries = r.get("target_countries") or []
        if countries and (user_country not in countries):
            continue
        genders = r.get("target_genders") or []
        if genders and (user_gender not in genders):
            continue
        candidates.append(r)

    if not candidates:
        return JSONResponse(status_code=204, content={"message": "no surveys"})

    survey = candidates[0]
    items_q = (
        supabase.table("survey_items")
        .select("id,body,is_exclusive,position,lang")
        .eq("survey_id", survey["id"])
        .eq("lang", survey["lang"])
    )
    try:
        items_q = items_q.order("position")
    except AttributeError:
        pass
    items = items_q.execute().data or []
    items.sort(key=lambda it: it.get("position", 0))

    survey["items"] = items

    if user_id:
        try:
            log_event(user_id, "survey_start", {"lang": lang, "nationality": user_country})
        except Exception:  # pragma: no cover - logging only
            pass
    return {"survey": survey, "items": items}


@app.get("/surveys")
async def public_surveys(lang: str = "en"):
    return {"questions": get_surveys(lang)}


@app.post("/survey/submit")
async def survey_submit(payload: SurveySubmit):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers provided")

    answer = payload.answers[0]
    item_uuid_list = answer.item_ids or []
    if not item_uuid_list:
        items_q = (
            supabase_admin.table("survey_items")
            .select("id,position")
            .eq("survey_id", str(payload.survey_id))
        )
        try:
            items_q = items_q.order("position")
        except AttributeError:
            pass
        items = items_q.execute().data or []
        idx_map = [row["id"] for row in items]
        selections = answer.selections or []
        item_uuid_list = [idx_map[i] for i in selections if 0 <= i < len(idx_map)]
    if not item_uuid_list:
        return JSONResponse({"error": "no_selection"}, status_code=400)

    rows = [
        {
            "survey_id": str(payload.survey_id),
            "survey_group_id": str(payload.survey_group_id),
            "survey_item_id": str(item_id),
            "user_id": str(payload.user_id) if payload.user_id else None,
        }
        for item_id in item_uuid_list
    ]

    supabase_admin.table("survey_answers").upsert(
        rows, on_conflict="user_id,survey_item_id"
    ).execute()

    if payload.user_id:
        supabase_admin.table("app_users").update({"survey_completed": True}).eq(
            "id", str(payload.user_id)
        ).execute()

    return {"status": "ok"}

class UserAction(BaseModel):
    user_id: str


@app.post("/survey/complete")
async def survey_complete(action: UserAction):
    supabase = get_supabase()
    db_update_user(supabase, action.user_id, {"survey_completed": True})
    return {"status": "ok"}


@app.post("/user/demographics")
async def user_demographics(info: DemographicInfo):
    """Collect demographic information and store securely."""
    await collect_demographics(
        info.age_band,
        info.gender,
        info.income_band,
        info.occupation,
        info.user_id,
    )
    return {"status": "ok"}




@app.get("/user/stats/{user_id}", response_model=UserStats)
async def user_stats(user_id: str):
    """Return play counts and history for a user."""
    max_free_attempts = await get_setting("max_free_attempts", 1)
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "plays": user.get("plays", 0),
        "referrals": user.get("referrals", 0),
        "scores": user.get("scores") or [],
        "party_log": user.get("party_log") or [],
        "free_attempts": min(user.get("free_attempts", max_free_attempts), max_free_attempts),
    }


@app.get("/user/history/{user_id}", response_model=HistoryResponse)
async def user_history(user_id: str):
    """Return past quiz scores for the user sorted by timestamp desc."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    scores = user.get("scores") or []
    scores = sorted(
        scores,
        key=lambda s: s.get("timestamp") or "",
        reverse=True,
    )
    return {"scores": scores}


@app.get("/points/{user_id}")
async def points_balance(user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"points": user.get("points", 0)}


@app.post("/analytics")
async def analytics(event: dict):
    """Log client-side events to self-hosted analytics."""
    import logging
    logging.getLogger(__name__).info("Event: %s", event)
    track_event(event)
    EVENTS.append(event)
    return {}


@app.get("/stats/iq_histogram")
async def iq_histogram(user_id: str):
    users = get_all_users()
    top_scores = []
    user_score = None
    for u in users:
        uscores = [s.get("iq") for s in (u.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        top_scores.append(top)
        if u.get("hashed_id") == user_id:
            user_score = top
    if not top_scores:
        return {
            "histogram": [],
            "bucket_edges": [],
            "user_score": user_score,
            "user_percentile": None,
        }
    min_edge = int(min(top_scores) // 5 * 5)
    max_edge = int(max(top_scores) // 5 * 5) + 5
    bucket_edges = list(range(min_edge, max_edge + 1, 5))
    hist_counts = [0] * (len(bucket_edges) - 1)
    for s in top_scores:
        idx = min(int((s - min_edge) // 5), len(hist_counts) - 1)
        hist_counts[idx] += 1
    percentile = None
    if user_score is not None:
        rank = sum(1 for s in top_scores if s <= user_score)
        percentile = rank / len(top_scores) * 100
    return {
        "histogram": hist_counts,
        "bucket_edges": bucket_edges,
        "user_score": user_score,
        "user_percentile": percentile,
    }


@app.get("/stats/survey_options/{group_id}")
async def survey_option_stats(group_id: str):
    answers = get_survey_answers(group_id)
    if not answers:
        return {"options": [], "averages": [], "counts": []}
    users = {u["hashed_id"]: u for u in get_all_users()}
    survey = next(
        (s for s in get_surveys("en") if s.get("group_id") == group_id),
        None,
    )
    if not survey:
        survey = next(
            (s for s in get_surveys() if s.get("group_id") == group_id),
            None,
        )
    options = survey.get("options", []) if survey else []
    iq_by_option: dict[int, list[float]] = {i: [] for i in range(len(options))}
    for ans in answers:
        user = users.get(ans["user_id"])
        if not user:
            continue
        uscores = [s.get("iq") for s in (user.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        iq_by_option.setdefault(ans["option_index"], []).append(top)
    averages = []
    counts = []
    for i in range(len(options)):
        vals = iq_by_option.get(i, [])
        counts.append(len(vals))
        averages.append(sum(vals) / len(vals) if vals else 0)
    return {"options": options, "averages": averages, "counts": counts}


@app.get("/stats/distribution")
async def stats_distribution(user_id: str, epsilon: float = 1.0):
    """Return histogram of top IQ scores and user's percentile."""
    users = get_all_users()
    scores = []
    user_score = None
    for u in users:
        uscores = [s.get("iq") for s in (u.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        scores.append(top)
        if u.get("hashed_id") == user_id:
            user_score = top

    scores.sort()
    buckets: dict[int, int] = {}
    for s in scores:
        b = int(s // 5 * 5)
        buckets[b] = buckets.get(b, 0) + 1
    histogram = [{"bin": k, "count": v} for k, v in sorted(buckets.items())]
    mean = dp_average(scores, epsilon, min_count=MIN_BUCKET_SIZE)
    percentile = None
    if user_score is not None and scores:
        rank = sum(1 for s in scores if s <= user_score)
        percentile = rank / len(scores) * 100
    return {
        "histogram": histogram,
        "mean": mean,
        "user_score": user_score,
        "percentile": percentile,
    }


@app.get("/data/iq")
async def dp_data_api(
    api_key: str,
    age_band: str | None = None,
    gender: str | None = None,
    income_band: str | None = None,
):
    """Return aggregated IQ stats for paying clients with differential privacy."""

    if api_key != os.getenv("DATA_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Invalid API key")

    epsilon = float(os.getenv("DP_EPSILON", "1.0"))
    scores: List[float] = []
    users = get_all_users()
    for user in users:
        demo = user.get("demographic") or {}
        if age_band and demo.get("age_band") != age_band:
            continue
        if gender and demo.get("gender") != gender:
            continue
        if income_band and demo.get("income_band") != income_band:
            continue
        for s in (user.get("scores") or []):
            scores.append(s.get("iq"))

    if len(scores) < MIN_BUCKET_SIZE:
        raise HTTPException(status_code=400, detail="Not enough data")

    mean = dp_average(scores, epsilon, min_count=MIN_BUCKET_SIZE)
    if mean is None:
        raise HTTPException(status_code=400, detail="Not enough data")

    return {"count": len(scores), "avg_iq": mean}


@app.post("/admin/update-norms", dependencies=[Depends(require_admin)])
async def admin_update_norms():
    """Update normative distribution from stored user scores."""

    scores: List[float] = []
    users = get_all_users()
    for user in users:
        for s in (user.get("scores") or []):
            scores.append(s.get("iq"))
    update_normative_distribution(scores)
    return {"added": len(scores)}


@app.get("/admin/dif-report", dependencies=[Depends(require_admin)])
async def admin_dif_report():
    """Return DIF report for question bias analysis."""
    path = os.getenv("DIF_DATA_FILE", "data/responses.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No data")
    report = dif_report(path)
    return {"dif": report}


@app.post("/admin/upload-questions", dependencies=[Depends(require_admin)])
async def admin_upload_questions(payload: QuestionUpload):
    """Import a list of questions using the CLI helper."""

    if not isinstance(payload.questions, list):
        raise HTTPException(status_code=400, detail="Field 'questions' must be a list of objects")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "upload.json"
        tmp_path.write_text(json.dumps(payload.questions, ensure_ascii=False), encoding="utf-8")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                import_dir(Path(tmpdir))
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))
        log = f.getvalue().strip()

    return {"status": "success", "log": log}


@app.get("/admin/question-bank-info", dependencies=[Depends(require_admin)])
async def admin_question_bank_info():
    """Return metadata about the current question bank."""
    bank_path = Path(__file__).resolve().parent / "data" / "question_bank.json"
    try:
        with bank_path.open() as f:
            data = json.load(f)
        return {"count": len(data)}
    except FileNotFoundError:
        return {"count": 0}


@app.get("/share/meta")
async def share_meta():
    return {
        "hashtags": ["IQArena", "IQアリーナ"],
        "page": "results",
        "utm": {},
    }


