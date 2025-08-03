import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure backend package is on the path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
from deps.supabase_client import get_supabase_client  # type: ignore

logger = logging.getLogger(__name__)


def load_questions(directory: Path) -> list[dict]:
    questions: list[dict] = []
    for file in sorted(directory.glob('*.json')):
        with open(file, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            if isinstance(data, list):
                questions.extend(data)
            else:
                logger.warning('Skipping %s: expected a list of questions', file)
    return questions


def import_questions(directory: Path) -> None:
    if not directory.exists():
        logger.error('Directory %s does not exist', directory)
        return
    records = load_questions(directory)
    if not records:
        logger.info('No questions found in %s', directory)
        return
    client = get_supabase_client()
    client.table('questions').insert(records).execute()
    logger.info('Inserted %d questions', len(records))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Import question JSON files into Supabase')
    parser.add_argument('--dir', default='tests/questions', help='Directory containing JSON files')
    args = parser.parse_args()
    import_questions(Path(args.dir))
