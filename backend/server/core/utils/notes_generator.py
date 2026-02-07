import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_notes(transcript):

    if not transcript or len(transcript.split()) < 80:
        return "Not enough content to generate notes."

    prompt = f"""
Create CLEAN STUDY NOTES from this lecture.

FORMAT STRICTLY:

# Title

## Key Concepts
- point
- point

## Explanation
short paragraph

## Important Terms
- term : meaning

## Summary
3-4 lines

TEXT:
{transcript}
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=900
        )

        return res.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {e}"
