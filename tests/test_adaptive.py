import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from questions import get_balanced_random_questions
from adaptive import select_next_question, should_stop
from irt import update_theta


def test_adaptive_progress():
    pool = get_balanced_random_questions(20)
    theta = 0.0
    asked = []
    answers = []
    first_b = None
    for _ in range(10):
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
    assert avg_b >= first_b
