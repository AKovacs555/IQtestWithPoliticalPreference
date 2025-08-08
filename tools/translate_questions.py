"""Translate IQ question sets into multiple languages using OpenAI."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import openai

MODEL = os.getenv("TRANSLATION_MODEL", "gpt-4o")

def translate_item(question: str, options: list[str], target_lang: str) -> tuple[str, list[str]]:
    """Return the question and options translated into ``target_lang``."""

    system_prompt = (
        f"Translate the following IQ test question and its multiple-choice options into {target_lang}. "
        "Preserve the numbering/order of the options. Respond in JSON with keys 'question' and 'options'."
    )
    user_content = json.dumps({"question": question, "options": options}, ensure_ascii=False)
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
    except Exception as e:  # broad catch to surface API issues
        raise RuntimeError(f"OpenAI API call failed: {e}") from e

    text = resp.choices[0].message.content
    data = json.loads(text)
    return data["question"], data["options"]


def translate_file(path: Path, languages: list[str]) -> None:
    """Translate ``path`` into each language in ``languages`` and write files."""

    base_data = json.loads(path.read_text(encoding="utf-8"))
    set_id = base_data.get("id", path.stem)
    for lang in languages:
        print(f"Translating {set_id} -> {lang}")
        data = json.loads(json.dumps(base_data))  # deep copy
        data["language"] = lang
        for q in data.get("questions", []):
            qid = q.get("id")
            print(f"  question {qid}")
            translated_q, translated_opts = translate_item(q["question"], q["options"], lang)
            q["question"] = translated_q
            q["options"] = translated_opts
            time.sleep(1)
        out_file = path.parent / f"{set_id}_{lang}.json"
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="base question set JSON file")
    parser.add_argument("--languages", required=True, help="comma separated target languages")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY environment variable not set")
    openai.api_key = api_key

    languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    translate_file(Path(args.input), languages)


if __name__ == "__main__":
    main()
