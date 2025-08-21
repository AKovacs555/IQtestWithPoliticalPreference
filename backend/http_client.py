import os
import logging
import threading
import time
from typing import Optional
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception

logger = logging.getLogger(__name__)

_Client = httpx.Client
_client: Optional[_Client] = None


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes"}


def _should_retry(exc: Exception) -> bool:
    if isinstance(exc, (httpx.ReadError, httpx.ConnectError, httpx.PoolTimeout)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or 500 <= status < 600
    return False

_retry_deco = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(min=0.5, max=5.0),
    retry=retry_if_exception(_should_retry),
)


class RetryingClient(httpx.Client):
    """httpx.Client with tenacity-based retries for idempotent requests."""

    def request(self, method: str, url: str, *args, **kwargs) -> httpx.Response:  # type: ignore[override]
        idempotent = kwargs.pop("idempotent", False) or method.upper() in {"GET", "HEAD", "OPTIONS"}
        attempt = 0
        start = time.perf_counter()

        def send() -> httpx.Response:
            nonlocal attempt
            attempt += 1
            response = super(RetryingClient, self).request(method, url, *args, **kwargs)
            if response.status_code >= 500 or response.status_code == 429:
                raise httpx.HTTPStatusError("server error", request=response.request, response=response)
            return response

        try:
            if idempotent:
                response = _retry_deco(send)()
            else:
                response = send()
            latency = (time.perf_counter() - start) * 1000
            logger.info(
                "external_http", extra={"method": method.upper(), "path": urlparse(str(response.request.url)).path, "status": response.status_code, "attempt": attempt, "latency_ms": round(latency, 2)}
            )
            return response
        except Exception as exc:  # pragma: no cover - network error
            latency = (time.perf_counter() - start) * 1000
            logger.warning(
                "external_http_error",
                extra={
                    "method": method.upper(),
                    "path": urlparse(url).path,
                    "attempt": attempt,
                    "latency_ms": round(latency, 2),
                    "error": str(exc)[:200],
                },
            )
            raise


def get_client(transport: httpx.BaseTransport | None = None) -> RetryingClient:
    """Return a shared httpx client configured for Supabase REST.

    Connection pooling and timeout options follow the httpx documentation:
    https://www.python-httpx.org/advanced/#pool-limit-configuration
    """
    global _client
    if _client is None or _client.is_closed:
        base_url = os.getenv("BASE_REST_URL")
        if not base_url:
            supabase_url = os.getenv("SUPABASE_URL", "http://localhost").rstrip("/")
            base_url = f"{supabase_url}/rest/v1"
        timeout = httpx.Timeout(
            connect=float(os.getenv("HTTPX_CONNECT_TIMEOUT", 3.0)),
            read=float(os.getenv("READ_TIMEOUT", 10.0)),
            write=float(os.getenv("WRITE_TIMEOUT", 10.0)),
            pool=float(os.getenv("POOL_TIMEOUT", 5.0)),
        )
        limits = httpx.Limits(
            max_connections=int(os.getenv("MAX_CONNECTIONS", 20)),
            max_keepalive_connections=int(os.getenv("MAX_KEEPALIVE", 20)),
        )
        headers = {"User-Agent": "IQArenaBackend/1.0", "Accept": "application/json"}
        http2 = _env_bool("EXTERNAL_HTTP2", False)
        _client = RetryingClient(
            base_url=base_url,
            timeout=timeout,
            limits=limits,
            headers=headers,
            transport=transport,
            http2=http2,
        )
        if _env_bool("HTTPX_DEBUG", False):
            logging.getLogger("httpx").setLevel(logging.DEBUG)
    return _client


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def warmup_supabase() -> None:
    if not _env_bool("WARMUP_SUPABASE", False):
        return

    def _ping():
        try:
            get_client().options("/")
        except Exception:  # pragma: no cover - best effort
            logger.debug("supabase warmup failed", exc_info=True)

    threading.Thread(target=_ping, daemon=True).start()
