import os
import json
import logging
import openai

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.AsyncClient(api_key=api_key) if api_key else None

logger = logging.getLogger(__name__)


async def translate_question(
    question_text: str, options: list[str], target_lang: str
) -> tuple[str, list[str]]:
    """Translate a Japanese IQ question and its options into ``target_lang``."""

    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    prompt = (
        f"Translate the following Japanese IQ test question and its four options into {target_lang}. "
        "Return a JSON object with keys 'question' and 'options' (array of four strings). "
        "Do not include any markdown or code fences."
        f"\n\nQuestion: {question_text}\nOptions: {options}"
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
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
