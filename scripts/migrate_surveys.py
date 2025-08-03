import json
import uuid
import sys
from pathlib import Path

# Allow importing backend.db when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.db import insert_surveys, insert_parties  # noqa:E402


def main() -> None:
    data_path = ROOT / 'backend' / 'data' / 'surveys.json'
    with data_path.open() as f:
        data = json.load(f)

    groups: dict[str, str] = {}
    rows = []
    for item in data.get('questions', []):
        old_gid = str(item.get('group_id'))
        gid = groups.setdefault(old_gid, str(uuid.uuid4()))
        rows.append({
            'group_id': gid,
            'lang': item.get('lang'),
            'statement': item.get('statement'),
            'options': item.get('options', []),
            'type': item.get('type', 'sa'),
            'exclusive_options': item.get('exclusive_options', []),
            'lr': item.get('lr', 0.0),
            'auth': item.get('auth', 0.0),
        })

    insert_surveys(rows)
    insert_parties(data.get('parties', []))
    print(f"Inserted {len(rows)} survey rows and {len(data.get('parties', []))} parties")


if __name__ == '__main__':
    main()
