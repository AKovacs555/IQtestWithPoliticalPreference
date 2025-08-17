import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.deps.auth import get_current_user
from backend.deps.supabase_client import get_supabase_client
from backend.payment import create_nowpayments_invoice
from .dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-survey", tags=["custom-survey"])
admin_router = APIRouter(
    prefix="/admin/custom-survey",
    tags=["admin-custom-survey"],
    dependencies=[Depends(require_admin)],
)


@router.post("/apply")
async def apply_custom_survey(payload: dict, user: dict = Depends(get_current_user)):
    """Accept a custom survey request and create a payment intent."""
    supabase = get_supabase_client()
    invoice = create_nowpayments_invoice("5000", price_currency="JPY")
    data = {
        "user_id": user["hashed_id"],
        "data": payload.get("data"),
        "target_countries": payload.get("target_countries", []),
        "target_genders": payload.get("target_genders", []),
        "title": payload.get("title"),
        "payment_id": invoice.get("id") or invoice.get("payment_id"),
        "status": "pending",
    }
    resp = supabase.table("custom_survey_requests").insert(data).execute()
    request_id = resp.data[0]["id"] if resp.data else None
    return {"status": "pending", "request_id": request_id}


@admin_router.post("/{request_id}/approve")
async def approve_custom_survey(request_id: str):
    supabase = get_supabase_client()
    resp = (
        supabase.table("custom_survey_requests")
        .select("*")
        .eq("id", request_id)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Request not found")
    req = rows[0]
    survey_data = req.get("data", {})
    survey_data["target_countries"] = req.get("target_countries", [])
    survey_data["target_genders"] = req.get("target_genders", [])
    supabase.table("surveys").insert(survey_data).execute()
    supabase.table("custom_survey_requests").update({"status": "approved"}).eq(
        "id", request_id
    ).execute()
    return {"status": "approved"}


@admin_router.post("/{request_id}/reject")
async def reject_custom_survey(request_id: str):
    supabase = get_supabase_client()
    supabase.table("custom_survey_requests").update({"status": "rejected"}).eq(
        "id", request_id
    ).execute()
    return {"status": "rejected"}
