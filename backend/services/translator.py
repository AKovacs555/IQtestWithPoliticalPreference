import os, json
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

MODEL_DEFAULT = os.getenv("TRANSLATION_MODEL", "gpt-5")
client = AsyncOpenAI()

SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}},
        "answer_index": {"type": "integer"},
        "explanation": {"type": "string"}
    },
    "required": ["prompt", "options", "answer_index"],
    "additionalProperties": False
}
INSTRUCTIONS = (
    "You are a professional localization translator for psychometrics/IQ tests. "
    "Translate the input JSON from {src} to {tgt}. Preserve placeholders (e.g. {{...}}, %s, %(...)s), "
    "formatting (Markdown/LaTeX), numbers, option order, and answer_index. "
    "Return ONLY a JSON object following the provided schema."
)

def _normalize(q: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prompt": q.get("prompt", ""),
        "options": q.get("options", []),
        "answer_index": q.get("answer_index", 0),
        "explanation": q.get("explanation", "") or ""
    }

async def translate_one(
    q: Dict[str, Any],
    src_lang: str,
    tgt_lang: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    m = model or MODEL_DEFAULT
    user_input = json.dumps(_normalize(q), ensure_ascii=False)

    # Use Chat Completions instead of the deprecated Responses API.
    response = await client.chat.completions.create(
        model=m,
        messages=[
            {"role": "system", "content": INSTRUCTIONS.format(src=src_lang, tgt=tgt_lang)},
            {"role": "user", "content": user_input},
        ],
        temperature=0.0,
        response_format={"type": "json_schema", "schema": SCHEMA},
    )

    data = json.loads(response.choices[0].message.content)
    data.setdefault("explanation", "")
    return data

async def translate_batch(
    items: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    model: Optional[str] = None
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for q in items:
        out.append(await translate_one(q, src_lang, tgt_lang, model=model))
    return out
