import os
import json
import random
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

META_PATH = os.path.join(os.path.dirname(__file__), "quiz_meta.json")


# ==================================================
# META HELPERS
# ==================================================
def load_meta():
    if not os.path.exists(META_PATH):
        return {}
    try:
        with open(META_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def save_meta(data):
    with open(META_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_attempt(video_id):
    return load_meta().get(video_id, 0)


def increase_attempt(video_id):
    meta = load_meta()
    meta[video_id] = meta.get(video_id, 0) + 1
    save_meta(meta)


# ==================================================
# TEXT HELPERS
# ==================================================
def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_similar(q1, q2):
    return normalize(q1)[:60] == normalize(q2)[:60]


def split_transcript(transcript, chunk_words=140):
    words = transcript.split()
    chunks = []

    for i in range(0, len(words), chunk_words):
        part = words[i:i + chunk_words]
        if len(part) > 45:
            chunks.append(" ".join(part))

    return chunks


# ==================================================
# PROMPTS
# ==================================================
BASIC_PROMPT = """
Create 2 STANDARD MCQ questions:
- simple concept based
- beginner friendly
- avoid code output questions
- 4 options each
"""


STYLE_PROMPTS = [
"""
Create 1 CONCEPT MCQ:
- definition / purpose based
""",
"""
Create 1 SCENARIO MCQ:
- real life usage
""",
"""
Create 1 OUTPUT MCQ:
- predict result
""",
"""
Create 1 TRUE/FALSE MCQ with options:
["True","False","Cannot determine","Partially true"]
"""
]


# ==================================================
# CORE
# ==================================================
def clean_json(text):
    text = text.replace("```json", "").replace("```", "")
    text = text.strip()

    # sometimes model adds extra text
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:
        text = text[start:end+1]

    return text


def call_llm(prompt):

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=650
    )

    return response.choices[0].message.content.strip()


def generate_quiz(transcript, video_id, max_questions=6):

    if not transcript or len(transcript.split()) < 80:
        return []

    attempt = get_attempt(video_id)

    chunks = split_transcript(transcript)
    random.shuffle(chunks)

    collected = []
    used_questions = []

    for chunk in chunks:

        if len(collected) >= max_questions:
            break

        style = BASIC_PROMPT if attempt == 0 else random.choice(STYLE_PROMPTS)

        prompt = f"""
{style}

STRICT RULES:
- MUST be from TEXT only
- Do NOT repeat earlier questions
- Return ONLY JSON array

FORMAT:
[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct_index": 0
  }}
]

TEXT:
{chunk}
"""

        try:
            raw = call_llm(prompt)

            raw = clean_json(raw)

            questions = json.loads(raw)

            for q in questions:

                if not q.get("question") or not q.get("options"):
                    continue

                if len(q["options"]) != 4:
                    continue

                if not any(is_similar(q["question"], u) for u in used_questions):

                    collected.append(q)
                    used_questions.append(q["question"])

                if len(collected) >= max_questions:
                    break

        except Exception as e:
            print("QUIZ ERROR:", e)
            continue

    increase_attempt(video_id)

    random.shuffle(collected)
    return collected
