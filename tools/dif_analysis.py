"""Simple DIF analysis helper.

This script expects a CSV file with columns:
user_id,question_id,correct,group
"""
import csv
from collections import defaultdict
from typing import Dict


def dif_report(path: str) -> Dict[int, float]:
    counts = defaultdict(lambda: [0, 0])
    totals = defaultdict(lambda: [0, 0])
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = int(row["question_id"])
            g = row["group"]
            idx = 0 if g == "A" else 1
            totals[q][idx] += 1
            counts[q][idx] += int(row["correct"])
    dif = {}
    for q in counts:
        c0, c1 = counts[q]
        t0, t1 = totals[q]
        if t0 >= 50 and t1 >= 50:
            p0 = c0 / t0
            p1 = c1 / t1
            dif[q] = round(p0 - p1, 3)
    return dif

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="response CSV")
    args = ap.parse_args()
    print(dif_report(args.csv))
