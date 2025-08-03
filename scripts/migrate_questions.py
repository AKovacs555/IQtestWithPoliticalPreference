import json
import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.db import insert_questions  # noqa:E402


def main() -> None:
    data_path = ROOT / 'backend' / 'data' / 'question_bank_backup.json'
    if not data_path.exists():
        raise SystemExit('question_bank_backup.json not found')
    with data_path.open() as f:
        data = json.load(f)

    rows = []
    for item in data:
        gid = str(uuid.uuid4())
        rows.append({
            'group_id': gid,
            'lang': item.get('lang', 'en'),
            'question': item['question'],
            'options': item['options'],
            'answer': item['answer'],
            'irt_a': item.get('irt', {}).get('a'),
            'irt_b': item.get('irt', {}).get('b'),
            'image': item.get('image'),
            'image_prompt': item.get('image_prompt'),
        })

    insert_questions(rows)
    print(f"Inserted {len(rows)} questions")


if __name__ == '__main__':
    main()
