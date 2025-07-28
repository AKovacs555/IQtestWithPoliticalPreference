import os, sys, json
from pathlib import Path
from jsonschema import validate

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from questions import (
    get_balanced_random_questions,
    get_balanced_random_questions_by_set,
)
from adaptive import select_next_question, should_stop
from irt import update_theta

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'questions' / 'schema.json'


def _sample_questions():
    qs = []
    for i in range(30):
        b = -1.0 if i < 10 else (0.0 if i < 20 else 1.0)
        qs.append({"id": i, "irt": {"a": 1.0, "b": b}})
    return qs


def test_schema_validation():
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    sample = {
        "id": "test",
        "language": "en",
        "title": "Unit",
        "questions": [
            {
                "id": 0,
                "question": "Test?",
                "options": ["a", "b", "c", "d"],
                "answer": 0,
                "irt": {"a": 1.0, "b": 0.0}
            }
        ]
    }
    validate(sample, schema)


def test_balanced_sampling(monkeypatch):
    sample = _sample_questions()
    monkeypatch.setattr('questions.QUESTION_MAP', {q['id']: q for q in sample}, raising=False)
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
    assert abs(counts['easy'] - 8 * 0.3) <= 1
    assert abs(counts['medium'] - 8 * 0.4) <= 1
    assert abs(counts['hard'] - 8 * 0.3) <= 1


def test_balanced_sampling_by_set(monkeypatch):
    sample = _sample_questions()
    monkeypatch.setattr('questions.load_questions', lambda sid: sample)
    qs = get_balanced_random_questions_by_set(1, 'set01')
    assert len(qs) == 1


def test_adaptive_stop(monkeypatch):
    sample = _sample_questions()
    monkeypatch.setattr('questions.QUESTION_MAP', {q['id']: q for q in sample}, raising=False)
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
