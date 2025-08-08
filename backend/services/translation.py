import os
import logging
from typing import Optional

from openai import OpenAI, BadRequestError, APIError, RateLimitError

logger = logging.getLogger(__name__)

_MODEL = os.getenv("TRANSLATION_MODEL", "gpt-5")
_FALLBACK_MODEL = os.getenv("TRANSLATION_FALLBACK_MODEL", "gpt-4o")
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test"))


def is_reasoning(model: str) -> bool:
    """Return True if the model is a reasoning model."""
    return any(x in model for x in ["gpt-5", "o3", "reason"])


def translate_text(
    text: str,
    src_lang: str,
    dst_lang: str,
    system_hint: Optional[str] = None,
) -> str:
    """Translate arbitrary text using OpenAI models.

    For reasoning models like gpt-5 the Responses API is used without any sampling
    parameters. If the primary model is unavailable or returns a BadRequestError
    (such as unsupported parameters), the function retries and falls back to the
    model defined by ``TRANSLATION_FALLBACK_MODEL``.
    """

    sys = system_hint or (
        "You are a professional translator. Preserve meaning and tone, avoid adding explanations."
    )
    prompt = (
        f"Translate the following from {src_lang} to {dst_lang}. "
        f"Return only the translated text with no extra quotes or notes.\n\n{text}"
    )

    def _responses_call(model: str) -> str:
        resp = _client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": sys},
                {"role": "user", "content": prompt},
            ],
            max_output_tokens=2048,
        )
        return resp.output[0].content[0].text.strip()

    def _chat_call(model: str) -> str:
        comp = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=2048,
        )
        return comp.choices[0].message.content.strip()

    try:
        if is_reasoning(_MODEL):
            return _responses_call(_MODEL)
        return _chat_call(_MODEL)
    except BadRequestError as e:
        logger.warning("Retrying without sampling due to: %s", e)
        try:
            return _responses_call(_MODEL)
        except Exception as inner:
            logger.warning("Falling back to %s due to: %s", _FALLBACK_MODEL, inner)
            try:
                return _responses_call(_FALLBACK_MODEL)
            except Exception:
                return _chat_call(_FALLBACK_MODEL)
    except APIError as e:
        if getattr(e, "status_code", None) in (403, 404):
            logger.warning("Falling back to %s due to: %s", _FALLBACK_MODEL, e)
            try:
                return _responses_call(_FALLBACK_MODEL)
            except Exception:
                return _chat_call(_FALLBACK_MODEL)
        raise
    except RateLimitError:
        raise

