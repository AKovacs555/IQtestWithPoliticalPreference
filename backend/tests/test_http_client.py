import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.http_client import get_client, close_client


def _lifespan(transport):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app):
        get_client(transport=transport)
        yield
        close_client()

    return lifespan


def test_client_closed_on_shutdown():
    transport = httpx.MockTransport(lambda request: httpx.Response(200))
    app = FastAPI(lifespan=_lifespan(transport))
    with TestClient(app):
        client = get_client()
        assert not client.is_closed
    assert client.is_closed


def test_retry_on_read_error():
    calls = {"n": 0}

    def handler(request):
        if calls["n"] == 0:
            calls["n"] += 1
            raise httpx.ReadError("boom", request=request)
        calls["n"] += 1
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = get_client(transport=transport)
    resp = client.get("/")
    assert resp.json() == {"ok": True}
    assert calls["n"] == 2
    close_client()
