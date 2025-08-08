import os
import json
import logging
import openai


SUPPORTED_LANGUAGES = [
    "en",
    "ja",
    "es",
    "de",
    "it",
    "tr",
    "fr",
    "zh",
    "ko",
    "ar",
]

LANG_NAME_MAP = {
    "en": "English",
    "tr": "Turkish",
    "ru": "Russian",
    "zh": "Chinese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "de": "German",
    "ar": "Arabic",
    "ja": "Japanese",
}

TRANSLATION_MODEL = os.environ.get("TRANSLATION_MODEL", "gpt-4o")

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.AsyncClient(api_key=api_key) if api_key else None

logger = logging.getLogger(__name__)


async def translate_question(
    question_text: str, options: list[str], target_lang: str
) -> tuple[str, list[str]]:
    """Translate a Japanese IQ question and its options into ``target_lang``."""

    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    # Look up human-readable language name; fall back to code if unknown
    lang_name = LANG_NAME_MAP.get(target_lang, target_lang)

    prompt = (
        f"Translate the following Japanese IQ test question and its four options into {lang_name}. "
        "Return a JSON object with keys 'question' and 'options' (array of four strings). "
        "Do not include any markdown or code fences."
        f"\n\nQuestion: {question_text}\nOptions: {options}"
    )

    response = await client.chat.completions.create(
        model=TRANSLATION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1].strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()
    try:
        data = json.loads(content)
    except Exception as exc:
        logger.error(
            "Failed to parse translation for %s: %s\nRaw content: %s",
            target_lang,
            exc,
            content,
        )
        raise
    return data["question"], data["options"]


async def translate_survey(
    statement: str, options: list[str], target_lang: str
) -> tuple[str, list[str]]:
    """Translate a survey question and options into ``target_lang``.

    Parameters
    ----------
    statement:
        The question text in the source language.
    options:
        A list of option strings in the source language.
    target_lang:
        ISO language code to translate into.

    Returns
    -------
    tuple[str, list[str]]
        The translated statement and list of options.
    """

    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    lang_name = LANG_NAME_MAP.get(target_lang, target_lang)

    prompt = (
        "Translate the following survey question and its options into "
        f"{lang_name}. Question: {statement} Options: {options}. "
        "Return JSON {\"statement\":..., \"options\": [...]}."
    )

    response = await client.chat.completions.create(
        model=TRANSLATION_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1].strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()
    try:
        data = json.loads(content)
    except Exception as exc:
        logger.error(
            "Failed to parse translation for %s: %s\nRaw content: %s",
            target_lang,
            exc,
            content,
        )
        raise
    return data["statement"], data["options"]
