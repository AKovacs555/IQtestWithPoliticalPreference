import os
import openai

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key) if api_key else None

async def translate_question(question_text: str, options: list[str], target_lang: str) -> tuple[str, list[str]]:
    """Translate a Japanese IQ question and its options into ``target_lang``."""
    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    prompt = (
        f"Translate the following Japanese IQ test question and its four options into {target_lang}. "
        f"Return only the translated question and four options on separate lines.\n\n"
        f"Question: {question_text}\n"
        f"Options:\n"
        f"1. {options[0]}\n"
        f"2. {options[1]}\n"
        f"3. {options[2]}\n"
        f"4. {options[3]}\n"
    )
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    q_translated = lines[0]
    opts_translated = [lines[i] for i in range(1, 5)]
    return q_translated, opts_translated
