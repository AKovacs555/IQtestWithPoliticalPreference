import os, sys, json
from pathlib import Path
from jsonschema import validate

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from questions import get_balanced_random_questions
from adaptive import select_next_question, should_stop
from irt import update_theta

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'questions' / 'schema.json'


def test_schema_validation():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    item_schema = schema['properties']['questions']['items']
    sample = {
        "text": "Test?",
        "options": ["a", "b"],
        "correct_index": 0,
        "category": "logic",
        "difficulty": "easy",
        "needs_image": False,
        "irt": {"a": 1.0, "b": 0.0}
    }
    validate(sample, item_schema)


def test_balanced_sampling():
    qs = get_balanced_random_questions(8)
    counts = {1: 0, 2: 0, 3: 0}
    for q in qs:
        counts[q.get('difficulty', 2)] += 1
    assert abs(counts[1] - 8 * 0.3) <= 1
    assert abs(counts[2] - 8 * 0.4) <= 1
    assert abs(counts[3] - 8 * 0.3) <= 1


def test_adaptive_stop():
    pool = [q['id'] for q in get_balanced_random_questions(10)]
    theta = 0.0
    asked = []
    answers = []
    while True:
        q = select_next_question(theta, asked, pool)
        if q is None:
            break
        asked.append(q['id'])
        correct = False
        theta = update_theta(theta, q['irt']['a'], q['irt']['b'], correct)
        answers.append({'id': q['id'], 'answer': 0, 'correct': correct})
        if should_stop(theta, answers):
            break
    assert len(answers) <= 20
