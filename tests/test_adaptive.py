import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from adaptive import select_next_question, should_stop
from irt import update_theta


def _sample_pool(n=20):
    return [
        {
            "id": i,
            "irt": {"a": 1.0, "b": -1.0 + i * 0.1},
        }
        for i in range(n)
    ]


def test_adaptive_progress():
    pool = _sample_pool(20)
    theta = 0.0
    asked = []
    answers = []
    first_b = None
    for _ in range(20):
        q = select_next_question(theta, asked, pool)
        if not q:
            break
        asked.append(q['id'])
        theta = update_theta(theta, q['irt']['a'], q['irt']['b'], True)
        answers.append({'a': q['irt']['a'], 'b': q['irt']['b'], 'correct': True})
        if first_b is None:
            first_b = q['irt']['b']
        if should_stop(theta, answers):
            break
    avg_b = sum(a['b'] for a in answers) / len(answers)
    assert theta > 0
    assert len(answers) <= 20
    assert len(answers) > 0
