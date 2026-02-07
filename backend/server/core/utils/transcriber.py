import os
import whisper
import json

# Load tiny model – fast and enough for English lectures
model = whisper.load_model("tiny")

def transcribe_audio(audio_path):
    if not os.path.exists(audio_path):
        raise ValueError("Audio file not found")

    if os.path.getsize(audio_path) < 10000:
        raise ValueError("Audio file too small")

    result = model.transcribe(
        audio_path,
        fp16=False,                 # CPU safe
        language="en",
        verbose=False,
        condition_on_previous_text=False
    )

    text = result.get("text", "").strip()

    if not text:
        raise ValueError("No speech detected")

    # 🔥 NEW: Build timestamp transcript
    segments = result.get("segments", [])

    transcript = []

    for seg in segments:
        transcript.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })

    # Return both formats
    return {
        "full_text": text,
        "timeline": transcript
    }
