import json
import hmac
import hashlib
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import backend.main as main


def _sign(payload, secret):
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha512).hexdigest()


def test_nowpayments_callback_valid(monkeypatch):
    secret = "devsecret"
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", secret)

    processed = set()
    calls = []

    monkeypatch.setattr(main, "is_payment_processed", lambda pid: pid in processed)
    monkeypatch.setattr(main, "mark_payment_processed", lambda pid: processed.add(pid))
    monkeypatch.setattr(
        main, "increment_free_attempts", lambda uid, delta=1: calls.append((uid, delta))
    )

    client = TestClient(main.app)

    payload = {"payment_id": "p1", "payment_status": "finished", "order_id": "user"}
    sig = _sign(payload, secret)
    resp = client.post(
        "/payment/nowpayments/callback",
        json=payload,
        headers={"x-nowpayments-sig": sig},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert calls == [("user", 1)]

    # replay should not credit again
    resp2 = client.post(
        "/payment/nowpayments/callback",
        json=payload,
        headers={"x-nowpayments-sig": sig},
    )
    assert resp2.status_code == 200
    assert calls == [("user", 1)]


def test_nowpayments_callback_invalid_signature(monkeypatch):
    secret = "devsecret"
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", secret)

    calls = []
    monkeypatch.setattr(main, "increment_free_attempts", lambda uid, delta=1: calls.append((uid, delta)))
    monkeypatch.setattr(main, "is_payment_processed", lambda pid: False)
    monkeypatch.setattr(main, "mark_payment_processed", lambda pid: None)

    client = TestClient(main.app)

    payload = {"payment_id": "p2", "payment_status": "finished", "order_id": "user"}
    resp = client.post(
        "/payment/nowpayments/callback",
        json=payload,
        headers={"x-nowpayments-sig": "bad"},
    )
    assert resp.status_code == 401
    assert resp.json() == {"error": "invalid_signature"}
    assert calls == []
