import json
from pathlib import Path
import sys
from jsonschema import validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "questions" / "schema.json"
QUESTIONS_DIR = ROOT / "questions"


def validate_all() -> bool:
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    ok = True
    for path in QUESTIONS_DIR.glob("*.json"):
        if path.name == "schema.json":
            continue
        with path.open() as f:
            data = json.load(f)
        try:
            validate(data, schema)
        except ValidationError as e:
            print(f"{path.name}: {e.message}")
            ok = False
    return ok


if __name__ == "__main__":
    success = validate_all()
    if not success:
        sys.exit(1)
    print("All question files valid.")
