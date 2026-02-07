from rest_framework.decorators import api_view
from rest_framework.response import Response

import re
import json
from pathlib import Path

from .utils.youtube import download_audio
from .utils.transcriber import transcribe_audio  # ← NO CHANGE, same import!
from .utils.quiz_generator import generate_quiz
from .utils.notes_generator import generate_notes
from .utils.chatbot import answer_from_transcript

from .constants import LECTURE_VIDEOS


# ================= PATH SETUP =================
BASE_DIR = Path(__file__).resolve().parent
TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


# ================= HELPERS =================
def extract_video_id(url):
    patterns = [
        r"youtu\.be/([^?&]+)",
        r"v=([^?&]+)",
        r"embed/([^?&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_partial_transcript(full_transcript, watched_seconds):
    """
    Return transcript text based on watched duration
    """
    if not watched_seconds or watched_seconds <= 0:
        return " ".join(full_transcript.split()[:900])

    words_per_second = 2.5
    max_words = int(watched_seconds * words_per_second)
    return " ".join(full_transcript.split()[:max_words])


# ================= API ENDPOINTS =================

@api_view(["GET"])
def get_lectures(request):
    return Response(LECTURE_VIDEOS)


# ------------------------------------------------
@api_view(["POST"])
def submit_video(request):
    lecture_id = request.data.get("lecture_id")

    if not lecture_id or lecture_id not in LECTURE_VIDEOS:
        return Response({"error": "Invalid lecture_id"}, status=400)

    youtube_url = LECTURE_VIDEOS[lecture_id]["url"]
    video_id = extract_video_id(youtube_url)
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"

    try:
        if transcript_path.exists():
            return Response({
                "status": "success",
                "video_id": video_id,
                "message": "Transcript already exists"
            })

        # Download audio
        audio_path = download_audio(youtube_url)
        
        # 🔥 CHANGED: Pass youtube_url to transcribe_audio
        print(f"Processing: {youtube_url}")
        data = transcribe_audio(audio_path, youtube_url=youtube_url)
        
        print(f"✅ Method: {data.get('source', 'unknown')}")
        print(f"✅ Segments: {len(data.get('timeline', []))}")

        # Save transcript
        transcript_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        return Response({
            "status": "success",
            "video_id": video_id,
            "message": "Transcript generated",
            "method": data.get('source', 'unknown')
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["GET"])
def get_transcript(request, video_id):
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"

    if not transcript_path.exists():
        return Response({"error": "Transcript not found"}, status=404)

    try:
        content = transcript_path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):
            return Response(json.loads(content))

        return Response({"full_text": content})

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["POST"])
def generate_quiz_view(request):
    video_id = request.data.get("video_id")
    watched_seconds = request.data.get("watched_seconds", 0)

    if not video_id:
        return Response({"error": "Video ID required"}, status=400)

    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"
    if not transcript_path.exists():
        return Response({"error": "Transcript not found"}, status=400)

    try:
        content = transcript_path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):
            full_text = json.loads(content).get("full_text", "")
        else:
            full_text = content

        partial_text = get_partial_transcript(full_text, watched_seconds)
        quiz = generate_quiz(partial_text, video_id)

        if not quiz:
            return Response({"error": "Quiz generation failed"}, status=500)

        return Response({
            "status": "success",
            "quiz": quiz
        })

    except Exception as e:
        print("QUIZ ERROR >>>", e)
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["POST"])
def generate_notes_view(request):
    video_id = request.data.get("video_id")
    watched_seconds = request.data.get("watched_seconds", 0)
    mode = request.data.get("mode", "watched")  # watched | full

    if not video_id:
        return Response({"error": "Video ID required"}, status=400)

    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"
    if not transcript_path.exists():
        return Response({"error": "Transcript not found"}, status=400)

    try:
        content = transcript_path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):
            full_text = json.loads(content).get("full_text", "")
        else:
            full_text = content

        source_text = (
            get_partial_transcript(full_text, watched_seconds)
            if mode == "watched"
            else full_text
        )

        notes = generate_notes(
            source_text,
            title="Watched Notes" if mode == "watched" else "Full Lecture Notes",
            mode=mode
        )

        return Response({
            "status": "success",
            "mode": mode,
            "notes": notes
        })

    except Exception as e:
        print("NOTES ERROR >>>", e)
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["POST"])
def chatbot_view(request):
    video_id = request.data.get("video_id")
    question = request.data.get("question")

    if not video_id or not question:
        return Response(
            {"error": "video_id and question required"},
            status=400
        )

    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"
    if not transcript_path.exists():
        return Response({"error": "Transcript not found"}, status=404)

    try:
        content = transcript_path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):
            full_text = json.loads(content).get("full_text", "")
        else:
            full_text = content

        answer = answer_from_transcript(full_text, question)

        return Response({
            "status": "success",
            "answer": answer
        })

    except Exception as e:
        print("CHATBOT ERROR >>>", e)
        return Response({"error": str(e)}, status=500)