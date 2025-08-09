import os
import json
import hmac
import hashlib
import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .. import db

router = APIRouter(prefix="/payments/nowpayments", tags=["payments"])
logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"finished", "confirmed"}


def _sign_payload(payload: dict, secret: str) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha512).hexdigest()


@router.post("/ipn")
async def nowpayments_ipn(request: Request):
    secret = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"code": "INVALID_JSON"})

    signature = request.headers.get("x-nowpayments-sig", "")
    expected = _sign_payload(payload, secret)
    payment_id = str(payload.get("payment_id"))
    user_id = payload.get("order_id") or payload.get("user_id")
    log_extra: dict[str, Any] = {"payment_id": payment_id, "user_id": user_id}

    if not signature or not hmac.compare_digest(signature, expected):
        logger.warning("NOWPayments IPN bad signature", extra={"event": "ipn_bad_sig", **log_extra})
        return JSONResponse(status_code=400, content={"code": "BAD_SIGNATURE"})

    inserted = db.record_payment_event(
        payment_id=payment_id,
        user_id=user_id,
        status=payload.get("payment_status"),
        amount=payload.get("amount_paid"),
        currency=payload.get("pay_currency"),
        raw=payload,
    )
    if not inserted:
        logger.info("NOWPayments IPN replay", extra={"event": "ipn_replay", **log_extra})
        return JSONResponse(status_code=409, content={"code": "ALREADY_PROCESSED"})

    status = payload.get("payment_status")
    credited = False
    if status in TERMINAL_STATUSES and user_id:
        db.increment_free_attempts(user_id, 1)
        credited = True
        db.mark_payment_processed(payment_id)
        logger.info("NOWPayments IPN ok", extra={"event": "ipn_ok", **log_extra})

    return {"credited": credited}
