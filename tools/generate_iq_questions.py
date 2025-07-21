"""Utility to create IQ question sets using the o3pro model.

Usage:
    OPENAI_API_KEY=key python tools/generate_iq_questions.py --n 50 \
        --start_id 200 --outfile backend/data/iq_pool/new_set.json

The script prompts the model with a structured request to generate
`n` items in JSON format. IDs begin at ``start_id`` and must be unique
across all existing pool files. The output is validated before being
written to ``outfile``.
"""

import argparse
import json
import os
from pathlib import Path

import openai

from backend.questions import load_questions

MODEL = os.getenv("O3PRO_MODEL", "o3pro")
openai.api_key = os.getenv("OPENAI_API_KEY")

STRUCTURED_PROMPT = (
    "Generate {n} IQ test items formatted as JSON. Each item must have the "
    "fields: id, question, options (four), answer (0-3), difficulty (1-5), "
    "domain (pattern, logic, spatial, verbal, quantitative) and irt with "
    "parameters a between 0.5 and 2.5 and b between -2.0 and 2.0. Balance "
    "the domains and vary difficulties. Ensure the JSON array is valid."
)


def generate_items(n: int, start_id: int) -> list:
    prompt = STRUCTURED_PROMPT.format(n=n)
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content
    items = json.loads(text)
    for idx, it in enumerate(items):
        it["id"] = start_id + idx
    return items


def existing_ids() -> set:
    return {q["id"] for q in load_questions()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--start_id", type=int, required=True)
    parser.add_argument("--outfile", required=True)
    args = parser.parse_args()

    items = generate_items(args.n, args.start_id)
    collisions = existing_ids().intersection({it["id"] for it in items})
    if collisions:
        raise SystemExit(f"ID collision detected: {sorted(collisions)}")

    Path(args.outfile).write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {args.outfile}")


if __name__ == "__main__":
    main()
