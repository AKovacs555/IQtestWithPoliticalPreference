import os
import requests

NOWPAY_API_BASE = "https://api.nowpayments.io/v1"
NOWPAY_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")


def create_nowpayments_invoice(
    price_amount: str,
    price_currency: str = "USD",
    pay_currency: str | None = None,
    order_id: str | None = None,
):
    payload = {
        "price_amount": price_amount,
        "price_currency": price_currency,
        "pay_currency": pay_currency,
        "order_id": order_id,
        "ipn_callback_url": os.environ.get("NOWPAYMENTS_CALLBACK_URL"),
    }
    headers = {
        "x-api-key": NOWPAY_API_KEY,
        "Content-Type": "application/json",
    }
    resp = requests.post(
        f"{NOWPAY_API_BASE}/payment",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_nowpayments_status(payment_id: str):
    headers = {"x-api-key": NOWPAY_API_KEY}
    resp = requests.get(
        f"{NOWPAY_API_BASE}/payment/{payment_id}",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def select_processor(region: str) -> str:
    """Return an available payment processor."""
    if PAYPAL_CLIENT_ID and PAYPAL_SECRET:
        return "paypal"
    if NOWPAY_API_KEY:
        return "nowpayments"
    return ""
