import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ✅ THIS WAS MISSING OR MISNAMED EARLIER
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_notes(transcript, title="Lecture Notes", mode="watched"):
    """
    Generate clean, student-friendly notes.
    """

    if not transcript or len(transcript.split()) < 80:
        return "Not enough content to generate notes."

    # limit size (LLM safe)
    transcript = " ".join(transcript.split()[:1800])

    if mode == "watched":
        scope = "ONLY what the student has watched so far"
    else:
        scope = "the COMPLETE lecture content"

    prompt = f"""
You are a university professor creating EXAM-ORIENTED STUDY NOTES.

Rules:
- Simple English
- Beginner friendly
- Structured
- Easy to revise

Cover {scope}.

FORMAT STRICTLY IN MARKDOWN:

# {title}

## What You Will Learn
- 3 to 5 clear learning points

## Concept Explanation
Explain the topic in simple language (5–6 lines).

## Important Terms
- **Term** – simple meaning

## Key Takeaways
- 3 short bullet points

LECTURE CONTENT:
{transcript}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Notes generation failed: {e}"
