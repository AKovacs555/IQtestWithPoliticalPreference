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
    "Generate {n} IQ test questions referencing Spearman's g factor, fluid vs "
    "crystallized intelligence, and Raven's Progressive Matrices. Each item "
    "should include: question text, four answer options, the correct option "
    "index (0-3), an estimated difficulty on a 1-5 scale, and a short "
    "rationale. Use only original content."
)


def generate(n: int = 50):
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(n=n)}],
    )
    text = resp.choices[0].message.content
    items = json.loads(text)
    return items


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=50)
    parser.add_argument("-o", "--output", default="backend/data/question_bank.json")
    args = parser.parse_args()
    items = generate(args.n)
    with open(args.output, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} items to {args.output}")


if __name__ == "__main__":
    main()
