"""Generate IQ question items using the o3pro model.

This script sends a prompt to the language model to create batches of
questions in the JSON schema used by ``backend/data/iq_pool``.
The output should always be reviewed manually before being added to the
repository.
"""

import argparse
import json
import os
from pathlib import Path

import openai

PROMPT_TEMPLATE = (
    "Generate 50 diverse IQ test items similar to Raven\u2019s Progressive "
    "Matrices and other standardized tests. For each item, provide:\n"
    "- 'question': a clear description (use plain text or simple geometric patterns).\n"
    "- 'options': an array of four plausible answer choices.\n"
    "- 'answer': the index (0–3) of the correct option.\n"
    "- 'difficulty': an integer from 1 (easy) to 5 (hard).\n"
    "- 'domain': one of ['pattern', 'logic', 'spatial', 'verbal', 'quantitative'].\n"
    "- 'irt': an object with 'a' (discrimination parameter) between 0.5–2.5 and 'b' (difficulty parameter) between −2.0–2.0.\n"
    "The questions must not replicate any proprietary test content."
)

MODEL = os.getenv("O3PRO_MODEL", "o3pro")
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate(n: int) -> list:
    messages = [{"role": "user", "content": PROMPT_TEMPLATE.replace("50", str(n))}]
    resp = openai.ChatCompletion.create(model=MODEL, messages=messages)
    text = resp.choices[0].message.content
    return json.loads(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt_file", help="Path to custom prompt text", nargs="?")
    parser.add_argument("-n", type=int, default=50, help="Number of items")
    parser.add_argument("-o", "--output", default="iq_items.json")
    args = parser.parse_args()

    prompt = PROMPT_TEMPLATE
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    global PROMPT_TEMPLATE
    PROMPT_TEMPLATE = prompt

    items = generate(args.n)
    with open(args.output, "w") as f:
        json.dump(items, f, indent=2)
    print(f"Saved {len(items)} items to {args.output}")


if __name__ == "__main__":
    main()
