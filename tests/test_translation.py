import os
import sys
from openai import APIError, BadRequestError

sys.path.insert(0, os.path.abspath("backend"))
from services.translation import _client, is_reasoning, translate_text


class DummyResp:
    def __init__(self, text: str):
        self.output = [type("Choice", (), {"content": [type("Txt", (), {"text": text})()]})()]


def test_is_reasoning():
    assert is_reasoning("gpt-5") is True


def test_retry_without_sampling(monkeypatch):
    calls = {"count": 0}

    def fake_create(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            class DummyBadRequest(BadRequestError):
                def __init__(self):
                    self.status_code = 400

            raise DummyBadRequest()
        return DummyResp("こんにちは")

    monkeypatch.setattr(_client.responses, "create", fake_create)
    out = translate_text("hello", "en", "ja")
    assert out == "こんにちは"
    assert calls["count"] == 2


def test_fallback_to_gpt4o(monkeypatch):
    calls = []

    def fake_create(*args, **kwargs):
        calls.append(kwargs.get("model"))
        if len(calls) == 1:
            class DummyAPIError(APIError):
                def __init__(self, status_code):
                    self.status_code = status_code

            raise DummyAPIError(403)
        return DummyResp("hola")

    monkeypatch.setattr(_client.responses, "create", fake_create)
    result = translate_text("hello", "en", "es")
    assert result == "hola"
    assert calls[0] == "gpt-5"
    assert calls[1] != calls[0]

