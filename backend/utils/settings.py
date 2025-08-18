import logging
from typing import Any


logger = logging.getLogger(__name__)


def _fetch_setting(client: Any, key: str) -> Any | None:
    try:
        resp = (
            client.table("settings").select("value").eq("key", key).single().execute()
        )
        data = getattr(resp, "data", None)
        if data and data.get("value") is not None:
            return data["value"]
        logger.warning("Setting %s not found", key)
    except Exception as exc:  # pragma: no cover - network/db failures
        logger.warning("Error fetching setting %s: %s", key, exc)
    return None


def get_setting_int(client: Any, key: str, default: int) -> int:
    value = _fetch_setting(client, key)
    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning("Setting %s has non-int value %r", key, value)
    return default


def get_setting_bool(client: Any, key: str, default: bool) -> bool:
    v = get_setting_int(client, key, 1 if default else 0)
    return v != 0

