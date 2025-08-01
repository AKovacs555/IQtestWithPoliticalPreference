import os
import json
import openai

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.AsyncClient(api_key=api_key) if api_key else None


async def translate_question(
    question_text: str, options: list[str], target_lang: str
) -> tuple[str, list[str]]:
    """Translate a Japanese IQ question and its options into ``target_lang``."""

    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    prompt = (
        f"Translate the following Japanese IQ test question and its four options into {target_lang}. "
        "Return a JSON object with keys 'question' and 'options' (an array of 4 translated options). "
        "Do not include any other keys. Do not wrap your response in code fences.\n\n"
        f"Question: {question_text}\n"
        f"Options: {options}"
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    json_text = response.choices[0].message.content.strip()
    cleaned = json_text.replace("```", "").strip()
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    try:
        data = json.loads(cleaned)
    except Exception:
        raise RuntimeError(f"Failed to parse JSON translation: {json_text}")

    return data["question"], data["options"]
