import argparse
import json
import logging
import os
import sys
import uuid
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


def _upload_image(client, bucket: str, file_path: Path) -> str | None:
    if not file_path.exists():
        logger.warning("Image file %s not found", file_path)
        return None
    storage_path = f"{uuid.uuid4()}_{file_path.name}"
    with file_path.open("rb") as fh:
        client.storage.from_(bucket).upload(storage_path, fh.read(), {"upsert": True})
    return client.storage.from_(bucket).get_public_url(storage_path)


def import_questions(directory: Path) -> None:
    if not directory.exists():
        logger.error('Directory %s does not exist', directory)
        return
    records = load_questions(directory)
    if not records:
        logger.info('No questions found in %s', directory)
        return
    client = get_supabase_client()
    bucket = os.getenv("IQ_IMAGE_BUCKET", "iq-images")
    for q in records:
        img_file = q.pop("image_filename", None)
        if img_file:
            url = _upload_image(client, bucket, directory / img_file)
            if url:
                q["image"] = url
        option_files = q.pop("option_image_filenames", []) or []
        option_urls = []
        for fname in option_files:
            url = _upload_image(client, bucket, directory / fname)
            if url:
                option_urls.append(url)
        if option_urls:
            q["option_images"] = option_urls
    client.table('questions').insert(records).execute()
    logger.info('Inserted %d questions', len(records))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Import question JSON files into Supabase')
    parser.add_argument('--dir', default='tests/questions', help='Directory containing JSON files')
    args = parser.parse_args()
    import_questions(Path(args.dir))
