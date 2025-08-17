import asyncio
from typing import Dict, Any, List, Optional

from backend.services.translation import translate_text


def _normalize(q: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prompt": q.get("prompt", ""),
        "options": q.get("options", []),
        "answer_index": q.get("answer_index", 0),
        "explanation": q.get("explanation", "") or "",
    }


async def translate_one(
    q: Dict[str, Any],
    src_lang: str,
    tgt_lang: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    base = _normalize(q)
    tasks = [
        asyncio.to_thread(translate_text, base["prompt"], src_lang, tgt_lang),
        *[
            asyncio.to_thread(translate_text, opt, src_lang, tgt_lang)
            for opt in base["options"]
        ],
    ]
    if base["explanation"]:
        tasks.append(
            asyncio.to_thread(translate_text, base["explanation"], src_lang, tgt_lang)
        )
    results = await asyncio.gather(*tasks)
    prompt_tr = results[0]
    options_tr = results[1 : 1 + len(base["options"])]
    explanation_tr = results[-1] if base["explanation"] else ""
    return {
        "prompt": prompt_tr,
        "options": options_tr,
        "answer_index": base["answer_index"],
        "explanation": explanation_tr,
    }


async def translate_batch(
    items: List[Dict[str, Any]],
    src_lang: str,
    tgt_lang: str,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for q in items:
        out.append(await translate_one(q, src_lang, tgt_lang, model=model))
    return out

