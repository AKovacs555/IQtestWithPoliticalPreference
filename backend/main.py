from fastapi import FastAPI

import os
import sys

# Provide placeholder environment variables so importing this module does not
# fail when optional settings are absent (e.g. during smoke tests).
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

# Ensure modules within this directory can be imported without the
# ``backend.`` prefix for compatibility with legacy imports.
sys.path.append(os.path.dirname(__file__))

from backend.api import diagnostics
from backend.routes import (
    admin_import_questions,
    admin_pricing,
    admin_questions,
    admin_surveys,
    ads,
    arena,
    custom_survey,
    daily,
    exam,
    leaderboard,
    points,
    quiz,
    referral,
    settings,
    sms,
    surveys,
    survey_start,
    user,
    user_profile_bootstrap,
)

app = FastAPI()

# include routers
app.include_router(diagnostics.router)
app.include_router(admin_import_questions.router)
app.include_router(admin_pricing.router)
app.include_router(admin_questions.router)
app.include_router(admin_surveys.router)
app.include_router(ads.router)
app.include_router(arena.router)
app.include_router(custom_survey.router)
app.include_router(daily.router)
app.include_router(exam.router)
app.include_router(leaderboard.router)
app.include_router(points.router)
app.include_router(quiz.router)
app.include_router(referral.router)
app.include_router(settings.router)
app.include_router(sms.router)
app.include_router(surveys.router)
app.include_router(survey_start.router)
app.include_router(user.router)
app.include_router(user_profile_bootstrap.router)


@app.get("/ping")
def ping():
    return {"status": "ok"}
