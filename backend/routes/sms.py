import random
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.sms_service import send_otp

router = APIRouter(prefix="/sms", tags=["sms"])

class SendRequest(BaseModel):
    phone: str

class VerifyRequest(BaseModel):
    phone: str
    code: str

@router.post("/send")
async def send_sms(payload: SendRequest, request: Request):
    code = f"{random.randint(0, 999999):06d}"
    store = getattr(request.app.state, "otps", {})
    store[payload.phone] = code
    request.app.state.otps = store
    send_otp(payload.phone, code)
    return {"status": "sent"}

@router.post("/verify")
async def verify_sms(payload: VerifyRequest, request: Request):
    store = getattr(request.app.state, "otps", {})
    if store.get(payload.phone) != payload.code:
        raise HTTPException(status_code=400, detail="invalid_code")
    del store[payload.phone]
    request.app.state.otps = store
    return {"status": "verified"}
