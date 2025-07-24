"""Import question JSON files into the question bank.

This helper merges manually created question files into
``backend/data/question_bank.json``.  Each input file should contain
either a JSON array of question objects or an object with a ``questions``
array.  ``text`` and ``correct_index`` keys are converted to ``question``
and ``answer`` for compatibility with the backend schema.  If an ``irt``
object is missing, ``{"a": 1.0, "b": 0.0}`` is used.

Run::

    python tools/generate_questions.py --import_dir=generated_questions

The script validates each question against ``questions/schema.json``,
assigns sequential IDs and prints a summary of how many items were
imported per difficulty level.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from jsonschema import validate, ValidationError


BANK_PATH = Path("backend/data/question_bank.json")
SCHEMA_PATH = Path("questions/schema.json")


def _load_item_schema() -> Dict:
    """Return the item schema from :data:`SCHEMA_PATH`."""
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    return schema


def _load_bank() -> List[Dict]:
    if BANK_PATH.exists():
        with BANK_PATH.open() as f:
            return json.load(f)
    return []


def _save_bank(items: List[Dict]) -> None:
    BANK_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _difficulty_label(item: Dict) -> str:
    diff = item.get("difficulty")
    if isinstance(diff, str):
        return diff
    # fall back to IRT b parameter if difficulty label missing
    b = item.get("irt", {}).get("b", 0.0)
    if b <= -0.35:
        return "easy"
    if b >= 0.35:
        return "hard"
    return "medium"


def import_dir(path: Path) -> None:
    schema = _load_item_schema()
    bank = _load_bank()
    next_id = max((q["id"] for q in bank), default=-1) + 1
    counts = defaultdict(int)

    seen_ids = {q["id"] for q in bank}
    for json_file in sorted(path.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skipping {json_file.name}: {e}")
            continue

        items = data.get("questions") if isinstance(data, dict) else data
        if not isinstance(items, list):
            print(f"Skipping {json_file.name}: not a list of questions")
            continue

        for item in items:
            # validate using legacy keys
            validate_data = item.copy()
            if "question" in validate_data and "text" not in validate_data:
                validate_data["text"] = validate_data["question"]
            if "answer" in validate_data and "correct_index" not in validate_data:
                validate_data["correct_index"] = validate_data["answer"]
            try:
                validate(validate_data, schema)
            except ValidationError as e:
                print(f"Validation error in {json_file.name}: {e.message}")
                continue

            # convert legacy keys after validation
            if "text" in item and "question" not in item:
                item["question"] = item.pop("text")
            if "correct_index" in item and "answer" not in item:
                item["answer"] = item.pop("correct_index")

            item.setdefault("irt", {})
            item["irt"].setdefault("a", 1.0)
            if "b" not in item["irt"]:
                diff = item.get("difficulty", "medium")
                default_b = {"easy": -0.7, "hard": 0.7}.get(diff, 0.0)
                item["irt"]["b"] = default_b

            qid = item.get("id")
            if qid is None or qid in seen_ids:
                item["id"] = next_id
                next_id += 1
            else:
                item["id"] = qid
                seen_ids.add(qid)

            item.pop("needs_image", None)

            bank.append(item)
            counts[_difficulty_label(item)] += 1

    _save_bank(bank)

    total = sum(counts.values())
    print(f"Imported {total} questions into {BANK_PATH}")
    for diff, c in counts.items():
        print(f"  {diff}: {c}")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--import_dir", type=str, help="directory of JSON files to import")
    args = ap.parse_args()

    if args.import_dir:
        import_dir(Path(args.import_dir))
    else:
        ap.error("--import_dir is required")


if __name__ == "__main__":
    main()

