import openai
import os

openai.api_key = os.environ.get("OPENAI_API_KEY")

async def translate_question(question_text: str, options: list[str], target_lang: str) -> tuple[str, list[str]]:
    prompt = (
        f"Translate the following Japanese IQ test question and its four options into {target_lang}. "
        f"Return only the translation.\n\n"
        f"Question: {question_text}\n"
        f"Options:\n"
        f"1. {options[0]}\n"
        f"2. {options[1]}\n"
        f"3. {options[2]}\n"
        f"4. {options[3]}\n"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    q_translated = lines[0]
    opts_translated = [lines[i] for i in range(1, 5)]
    return q_translated, opts_translated
