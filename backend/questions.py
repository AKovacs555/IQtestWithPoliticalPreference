"""Question bank loader with psychometric metadata."""

import json
from pathlib import Path
from typing import List, Dict, Any

DATA_PATH = Path(__file__).parent / "data" / "question_bank.json"


def load_questions() -> List[Dict[str, Any]]:
    with DATA_PATH.open() as f:
        return json.load(f)


DEFAULT_QUESTIONS: List[Dict[str, Any]] = load_questions()
