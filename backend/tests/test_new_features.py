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
        "category": "論理",
        "difficulty": "easy",
        "needs_image": False,
        "irt": {"a": 1.0, "b": 0.0}
    }
    validate(sample, item_schema)


def test_balanced_sampling():
    qs = get_balanced_random_questions(8)
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for q in qs:
        b = q['irt']['b']
        if b <= -0.33:
            counts['easy'] += 1
        elif b <= 0.33:
            counts['medium'] += 1
        else:
            counts['hard'] += 1
    assert abs(counts['easy'] - 8 * 0.3) <= 2
    assert abs(counts['medium'] - 8 * 0.4) <= 2
    assert abs(counts['hard'] - 8 * 0.3) <= 2


def test_adaptive_stop():
    pool = get_balanced_random_questions(10)
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
        answers.append({'a': q['irt']['a'], 'b': q['irt']['b'], 'correct': correct})
        if should_stop(theta, answers):
            break
    assert len(answers) <= 20
