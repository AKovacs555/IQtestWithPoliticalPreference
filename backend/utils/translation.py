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
        "Return a JSON object with keys 'question' and 'options'. "
        "Do not include any markdown or code fences."
        f"\n\nQuestion: {question_text}\nOptions: {options}"
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    data = response.choices[0].message.content
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        content = data.strip()
        if content.startswith("```"):
            content = content.split("```", 2)[1].strip()
            if content.lower().startswith("json"):
                content = content[4:].strip()
        try:
            parsed = json.loads(content)
        except Exception:
            logger.error(f"Failed to parse JSON translation: {data}")
            raise
    return parsed["question"], parsed["options"]
