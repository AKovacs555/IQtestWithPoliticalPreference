from __future__ import annotations
from typing import Any, Sequence
import logging

log = logging.getLogger(__name__)


def extract_response_text(resp: Any) -> str:
    """
    Robustly extract text from OpenAI Responses API or Chat Completions responses.
    Prefers Responses API's aggregated `output_text`. Falls back gracefully.
    Raises ValueError if no usable text is found.
    """
    # 1) Responses API preferred path
    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    # 2) Responses API raw output list (defensive)
    output = getattr(resp, "output", None)
    if isinstance(output, Sequence) and output:
        try:
            # Expect message -> content[] with {type: 'output_text', text: ...}
            first = output[0]
            content = getattr(first, "content", None) or (first.get("content") if isinstance(first, dict) else None)
            if isinstance(content, Sequence):
                for c in content:
                    # pydantic objects or dicts
                    ctype = getattr(c, "type", None) or (c.get("type") if isinstance(c, dict) else None)
                    if ctype in ("output_text", "text"):
                        t = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else None)
                        if isinstance(t, str) and t.strip():
                            return t.strip()
        except Exception:
            pass

    # 3) Chat Completions fallback shape
    choices = getattr(resp, "choices", None)
    if isinstance(choices, Sequence) and choices:
        msg = getattr(choices[0], "message", None) or (choices[0].get("message") if isinstance(choices[0], dict) else None)
        if msg:
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
            if isinstance(content, str) and content.strip():
                return content.strip()
            # sometimes content is a list of parts
            if isinstance(content, Sequence):
                parts = []
                for p in content:
                    t = getattr(p, "text", None) or (p.get("text") if isinstance(p, dict) else None)
                    if t:
                        parts.append(t)
                if parts:
                    return "\n".join(parts).strip()

    # 4) As a last resort, try model_dump()/dict
    try:
        d = resp.model_dump()  # pydantic models
    except Exception:
        d = resp if isinstance(resp, dict) else None

    if isinstance(d, dict):
        if isinstance(d.get("output_text"), str) and d["output_text"].strip():
            return d["output_text"].strip()
        # chat-like dict
        ch = d.get("choices") or []
        if ch:
            msg = ch[0].get("message", {})
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

    # No usable text
    log.error(
        "Failed to extract text from OpenAI response; raw keys: %s",
        list(d.keys()) if isinstance(d, dict) else type(resp),
    )
    raise ValueError("No text content in OpenAI response")


import os, time
from openai import OpenAI
from httpx import HTTPError

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def translate_with_openai(prompt: str, *, model_env: str = "OPENAI_TRANSLATION_MODEL") -> str:
    """
    Calls OpenAI Responses API for translation.
    - Uses model from env (default: gpt-5-mini) with Responses API.
    - Omits 'temperature' for gpt-5* models to avoid 400.
    - Retries transient 5xx once with backoff.
    """
    model = os.getenv(model_env, "gpt-5-mini")
    kwargs: dict[str, Any] = {"model": model, "input": prompt}

    # GPT‑5 family does not support non-default temperature; omit it entirely.
    # For others you may tune temperature via env if desired.
    if not model.startswith("gpt-5"):
        try:
            temp = os.getenv("OPENAI_TEMPERATURE")
            if temp:
                kwargs["temperature"] = float(temp)
        except Exception:
            pass

    # Optional reasoning effort for gpt-5 family (harmless for others)
    if model.startswith("gpt-5"):
        kwargs["reasoning"] = {"effort": "medium"}

    # One retry on transient errors
    for attempt in range(2):
        try:
            resp = _client.responses.create(**kwargs)
            return extract_response_text(resp)
        except HTTPError as e:
            if attempt == 0 and (getattr(e.response, "status_code", 0) >= 500):
                time.sleep(0.6)
                continue
            raise
