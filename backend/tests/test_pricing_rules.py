import os, sys
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import main


def test_country_specific_pricing(monkeypatch):
    def fake_get_pricing_rule(country, product):
        if country == "JP" and product == "retry":
            return {"price_jpy": 111}
        if country == "JP" and product == "pro_month":
            return {"price_jpy": 222}
        return None
    monkeypatch.setattr(main, "get_pricing_rule", fake_get_pricing_rule)
    with TestClient(main.app) as client:
        r = client.get("/pricing/u1", headers={"cf-country": "JP"})
        assert r.status_code == 200
        data = r.json()
        assert data["retry_price"] == 111
        assert data["pro_price"] == 222
        assert data["currency"] == "JPY"


def test_pro_purchase_flow(monkeypatch):
    def fake_invoice(price_amount, price_currency, pay_currency, order_id):
        return {"invoice_url": "http://pay", "payment_id": "pid"}
    monkeypatch.setattr(main, "create_nowpayments_invoice", fake_invoice)
    monkeypatch.setattr(main, "select_processor", lambda region: "nowpayments")
    with TestClient(main.app) as client:
        r = client.post("/purchase", json={"user_id": "u1", "amount": 500, "pay_currency": "eth"})
        assert r.status_code == 200
        data = r.json()
        assert data["processor"] == "nowpayments"
        assert data["payment_url"] == "http://pay"
        assert data["payment_id"] == "pid"
