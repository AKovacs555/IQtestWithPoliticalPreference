import os, sys
sys.path.insert(0, os.path.abspath('backend'))
from questions import get_balanced_random_questions


def test_balance_counts():
    qs = get_balanced_random_questions(20)
    easy = [q for q in qs if q['irt']['b'] <= -0.33]
    medium = [q for q in qs if -0.33 < q['irt']['b'] <= 0.33]
    hard = [q for q in qs if q['irt']['b'] > 0.33]
    assert abs(len(easy) - 6) <= 2
    assert abs(len(medium) - 8) <= 2
    assert abs(len(hard) - 6) <= 2
