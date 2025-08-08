import asyncio
from backend.services import translator


def test_normalize_preserves_answer_index(monkeypatch):
    q = {"prompt": "1+1=?", "options": ["1", "2", "3"], "answer_index": 1, "explanation": ""}

    async def fake_translate_one(q, src_lang, tgt_lang, model=None):
        return {"prompt": "１＋１＝？", "options": ["１", "２", "３"], "answer_index": 1, "explanation": ""}

    monkeypatch.setattr(translator, "translate_one", fake_translate_one)
    out = asyncio.run(translator.translate_batch([q], "en", "ja"))
    assert out[0]["answer_index"] == 1
