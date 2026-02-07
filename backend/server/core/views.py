from rest_framework.decorators import api_view
from rest_framework.response import Response
import re
from pathlib import Path
import json

from .utils.youtube import download_audio
from .utils.transcriber import transcribe_audio
from .utils.quiz_generator import generate_quiz
from .utils.notes_generator import generate_notes
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
    Return transcript only for watched duration
    """
    if not watched_seconds or watched_seconds <= 0:
        return " ".join(full_transcript.split()[:900])

    words_per_second = 2.5
    max_words = int(watched_seconds * words_per_second)

    words = full_transcript.split()
    return " ".join(words[:max_words])


# ================= API ENDPOINTS =================

@api_view(["GET"])
def get_lectures(request):
    """
    Return available lectures
    """
    return Response(LECTURE_VIDEOS)


# ------------------------------------------------
@api_view(["POST"])
def submit_video(request):
    """
    Download audio + generate transcript if not exists
    """
    lecture_id = request.data.get("lecture_id")

    if not lecture_id:
        return Response({"error": "lecture_id required"}, status=400)

    if lecture_id not in LECTURE_VIDEOS:
        return Response({"error": "Invalid Lecture ID"}, status=400)

    youtube_url = LECTURE_VIDEOS[lecture_id]["url"]
    video_id = extract_video_id(youtube_url)

    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"

    try:
        if transcript_path.exists():
            return Response({
                "status": "success",
                "video_id": video_id,
                "title": LECTURE_VIDEOS[lecture_id]["title"],
                "message": "Transcript already exists"
            })

        audio_path = download_audio(youtube_url)
        data = transcribe_audio(audio_path)

        transcript_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

        return Response({
            "status": "success",
            "video_id": video_id,
            "message": "Transcript generated"
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["GET"])
def get_transcript(request, video_id):
    """
    Return transcript text
    """
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.txt"

    if not transcript_path.exists():
        return Response({"error": "Transcript not found"}, status=404)

    try:
        content = transcript_path.read_text(encoding="utf-8")

        if content.strip().startswith("{"):
            data = json.loads(content)
            return Response(data)

        return Response({"full_text": content})

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["POST"])
def generate_quiz_view(request):
    """
    Generate quiz from watched transcript
    """
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
            data = json.loads(content)
            full_text = data.get("full_text", "")
        else:
            full_text = content

        partial_text = get_partial_transcript(full_text, watched_seconds)

        quiz_data = generate_quiz(partial_text, video_id)

        if not quiz_data:
            return Response({"error": "Quiz generation failed"}, status=500)

        return Response({
            "status": "success",
            "quiz": quiz_data
        })

    except Exception as e:
        print("QUIZ ERROR >>>", e)
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------
@api_view(["POST"])
def generate_notes_view(request):
    """
    Generate adaptive notes (watched or full)
    """
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
            data = json.loads(content)
            full_text = data.get("full_text", "")
        else:
            full_text = content

        # 🔥 Adaptive source selection
        if mode == "watched":
            source_text = get_partial_transcript(full_text, watched_seconds)
            title = "Watched Lecture Notes"
        else:
            source_text = full_text
            title = "Complete Lecture Notes"

        notes = generate_notes(
            source_text,
            title=title,
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
