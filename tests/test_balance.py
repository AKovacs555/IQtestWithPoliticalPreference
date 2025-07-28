import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from questions import get_balanced_random_questions


def _sample_questions():
    qs = []
    for i in range(30):
        b = -1.0 if i < 10 else (0.0 if i < 20 else 1.0)
        qs.append({"id": i, "irt": {"a": 1.0, "b": b}})
    return qs


def test_balance_counts(monkeypatch):
    sample = _sample_questions()
    monkeypatch.setattr('questions.QUESTION_MAP', {q['id']: q for q in sample}, raising=False)
    qs = get_balanced_random_questions(20)
    easy_count = sum(q['irt']['b'] <= -0.33 for q in qs)
    assert abs(easy_count - 6) <= 1
