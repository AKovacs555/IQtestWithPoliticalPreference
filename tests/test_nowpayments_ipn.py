import json
import hmac
import hashlib
import os
import sys
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import backend.routes.nowpayments as nowp


def _sign(payload, secret):
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha512).hexdigest()


def _client():
    app = FastAPI()
    app.include_router(nowp.router)
    return TestClient(app)


def test_rejects_bad_signature(monkeypatch, caplog):
    secret = "s"
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", secret)
    credited = []
    monkeypatch.setattr(nowp.db, "record_payment_event", lambda *a, **k: True)
    monkeypatch.setattr(
        nowp.db, "increment_free_attempts", lambda uid, delta=1: credited.append((uid, delta))
    )
    client = _client()
    payload = {"payment_id": "p1", "payment_status": "finished", "order_id": "u1"}
    resp = client.post(
        "/payments/nowpayments/ipn",
        json=payload,
        headers={"x-nowpayments-sig": "bad"},
    )
    assert resp.status_code == 400
    assert resp.json() == {"code": "BAD_SIGNATURE"}
    assert credited == []
    assert any(r.__dict__.get("event") == "ipn_bad_sig" for r in caplog.records)


def test_credits_on_finished_once(monkeypatch, caplog):
    secret = "s"
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", secret)
    credited = []
    recorded = []

    def record(*a, **k):
        recorded.append(a)
        return True

    monkeypatch.setattr(nowp.db, "record_payment_event", record)
    monkeypatch.setattr(nowp.db, "mark_payment_processed", lambda pid: None)
    monkeypatch.setattr(
        nowp.db, "increment_free_attempts", lambda uid, delta=1: credited.append((uid, delta))
    )
    client = _client()
    payload = {"payment_id": "p2", "payment_status": "finished", "order_id": "u2"}
    sig = _sign(payload, secret)
    resp = client.post(
        "/payments/nowpayments/ipn",
        json=payload,
        headers={"x-nowpayments-sig": sig},
    )
    assert resp.status_code == 200
    assert resp.json() == {"credited": True}
    assert credited == [("u2", 1)]
    assert len(recorded) == 1
    assert any(r.__dict__.get("event") == "ipn_ok" for r in caplog.records)


def test_idempotent_on_replay(monkeypatch, caplog):
    secret = "s"
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("NOWPAYMENTS_IPN_SECRET", secret)
    credited = []
    seen = set()

    def record(payment_id, *rest, **kw):
        if payment_id in seen:
            return False
        seen.add(payment_id)
        return True

    monkeypatch.setattr(nowp.db, "record_payment_event", record)
    monkeypatch.setattr(nowp.db, "mark_payment_processed", lambda pid: None)
    monkeypatch.setattr(
        nowp.db, "increment_free_attempts", lambda uid, delta=1: credited.append((uid, delta))
    )
    client = _client()
    payload = {"payment_id": "p3", "payment_status": "finished", "order_id": "u3"}
    sig = _sign(payload, secret)
    resp1 = client.post(
        "/payments/nowpayments/ipn",
        json=payload,
        headers={"x-nowpayments-sig": sig},
    )
    resp2 = client.post(
        "/payments/nowpayments/ipn",
        json=payload,
        headers={"x-nowpayments-sig": sig},
    )
    assert resp1.status_code == 200
    assert resp1.json() == {"credited": True}
    assert resp2.status_code == 409
    assert resp2.json() == {"code": "ALREADY_PROCESSED"}
    assert credited == [("u3", 1)]
    assert any(r.__dict__.get("event") == "ipn_replay" for r in caplog.records)
