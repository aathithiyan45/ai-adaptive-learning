import os
import json
import random
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


META_PATH = os.path.join(os.path.dirname(__file__), "quiz_meta.json")


def load_meta():
    if not os.path.exists(META_PATH):
        return {}
    try:
        return json.load(open(META_PATH))
    except:
        return {}


def save_meta(data):
    json.dump(data, open(META_PATH, "w"), indent=2)


def get_attempt(video_id):
    meta = load_meta()
    return meta.get(video_id, 0)


def increase_attempt(video_id):
    meta = load_meta()
    meta[video_id] = meta.get(video_id, 0) + 1
    save_meta(meta)


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_similar(q1, q2):
    return normalize(q1)[:55] == normalize(q2)[:55]


def split_transcript(transcript, chunk_words=120):
    words = transcript.split()
    return [
        " ".join(words[i:i + chunk_words])
        for i in range(0, len(words), chunk_words)
        if len(words[i:i + chunk_words]) > 40
    ]


BASIC_PROMPT = """
Create 2 STANDARD MCQ questions from the text.
Beginner friendly.
4 options each.
"""


STYLE_PROMPTS = [
"Create 1 CONCEPT MCQ",
"Create 1 SCENARIO MCQ",
"Create 1 OUTPUT MCQ",
"Create 1 TRUE/FALSE MCQ"
]


# ==================================================
# 🔥 MAIN FUNCTION
# ==================================================
def generate_quiz(transcript, video_id, max_questions=6):

    if not transcript or len(transcript.split()) < 80:
        return []

    attempt = get_attempt(video_id)

    chunks = split_transcript(transcript)
    random.shuffle(chunks)

    collected = []
    used = []

    for chunk in chunks:

        if len(collected) >= max_questions:
            break

        prompt_style = BASIC_PROMPT if attempt == 0 else random.choice(STYLE_PROMPTS)

        prompt = f"""
{prompt_style}

Return ONLY JSON array.

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
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=600
            )

            raw = response.choices[0].message.content.strip()

            # ✅ CLEAN JSON
            raw = raw.replace("```json", "").replace("```", "").strip()

            questions = json.loads(raw)

            for q in questions:

                if not any(is_similar(q["question"], p) for p in used):

                    collected.append(q)
                    used.append(q["question"])

                if len(collected) >= max_questions:
                    break

        except Exception as e:
            print("QUIZ ERROR:", e)
            continue

    increase_attempt(video_id)

    random.shuffle(collected)
    return collected
