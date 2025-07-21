"""Utility to generate IQ questions via the o3pro model.

This script prompts an external generative model to produce
IQ test items using established psychometric theory. Each
item includes a rationale and difficulty estimate so that
reviewers can validate content before it enters the question
bank."""

import os
import json
import openai

MODEL = os.getenv("O3PRO_MODEL", "o3pro")
openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT = (
    "Using open psychometric theory such as Spearman's g and common formats "
    "like Raven's matrices, generate {n} original IQ test questions. Create "
    "a diverse mixture of item types including pattern recognition, logical "
    "reasoning and spatial reasoning. Return each question as JSON with the "
    "fields: 'question', 'options' (four strings), 'answer' (index 0-3), "
    "'difficulty' (1-5), 'rationale', and an 'irt' object containing "
    "discrimination 'a' and difficulty 'b'. Optionally tag questions with a "
    "'category' such as 'General IQ' or 'Spatial IQ'. Do not copy or "
    "paraphrase items from proprietary tests."
)

PROPRIETARY_KEYWORDS = [
    "wechsler",
    "wais",
    "wisc",
    "raven",
]


def generate(n: int = 60):
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(n=n)}],
    )
    text = resp.choices[0].message.content
    items = json.loads(text)
    return items


def filter_proprietary(items):
    filtered = []
    for it in items:
        content = json.dumps(it).lower()
        if any(k in content for k in PROPRIETARY_KEYWORDS):
            continue
        filtered.append(it)
    return filtered


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=60)
    parser.add_argument("-o", "--output", default="backend/data/question_bank.json")
    args = parser.parse_args()
    items = generate(args.n)
    items = filter_proprietary(items)
    # ensure sequential ids and include difficulty metadata
    for i, item in enumerate(items):
        item["id"] = i
    with open(args.output, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} filtered items to {args.output}")


if __name__ == "__main__":
    main()
