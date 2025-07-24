import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from questions import get_balanced_random_questions


def test_balance_counts():
    qs = get_balanced_random_questions(20)
    easy_count = sum(q['irt']['b'] <= -0.33 for q in qs)
    assert abs(easy_count - 6) <= 1
