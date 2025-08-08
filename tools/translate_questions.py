import argparse
import json
import os
import time
from pathlib import Path

from openai import OpenAI

client = OpenAI()
model = os.getenv("TRANSLATION_MODEL", "gpt-5")

SCHEMA = {
    "name": "Question",
    "schema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "options": {"type": "array", "items": {"type": "string"}},
            "answer_index": {"type": "integer"},
            "explanation": {"type": "string"},
        },
        "required": ["prompt", "options", "answer_index"],
        "additionalProperties": False,
    },
    "strict": True,
}


def translate_payload(payload: dict, src: str, tgt: str) -> dict:
    resp = client.responses.create(
        model=model,
        instructions=(
            f"Translate JSON from {src} to {tgt}. Preserve placeholders, formatting, numbers, option order, and answer_index. "
            "Return ONLY JSON following the schema."
        ),
        input=json.dumps(payload, ensure_ascii=False),
        text={"format": {"type": "json_schema", "json_schema": SCHEMA}},
    )
    return json.loads(resp.output_text)


def translate_file(path: Path, languages: list[str]) -> None:
    base_data = json.loads(path.read_text(encoding="utf-8"))
    set_id = base_data.get("id", path.stem)
    src_lang = base_data.get("language", "ja")
    for lang in languages:
        print(f"Translating {set_id} -> {lang}")
        data = json.loads(json.dumps(base_data))
        data["language"] = lang
        for q in data.get("questions", []):
            qid = q.get("id")
            print(f"  question {qid}")
            payload = {
                "prompt": q.get("question", ""),
                "options": q.get("options", []),
                "answer_index": q.get("answer", 0),
                "explanation": q.get("explanation", ""),
            }
            translated = translate_payload(payload, src_lang, lang)
            q["question"] = translated["prompt"]
            q["options"] = translated["options"]
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
    # OpenAI client picks up key from env automatically

    languages = [lang.strip() for lang in args.languages.split(",") if lang.strip()]
    translate_file(Path(args.input), languages)


if __name__ == "__main__":
    main()
