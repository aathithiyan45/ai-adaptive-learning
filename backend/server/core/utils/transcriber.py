"""
REPLACE your existing transcriber.py with THIS file
Location: backend/server/core/utils/transcriber.py

This combines Whisper + YouTube timing in your existing file
No new imports needed in views.py!
"""

from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import re
import os

# Load Whisper model
model = whisper.load_model("tiny")


def extract_video_id(url):
    """Extract video ID from YouTube URL"""
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


def get_youtube_timestamps(youtube_url):
    """
    Get ONLY timestamps from YouTube captions
    Returns perfect timing data
    """
    video_id = extract_video_id(youtube_url)
    
    if not video_id:
        return None
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['en', 'en-US', 'en-GB', 'hi', 'ta']
        )
        
        timestamps = []
        for entry in transcript_list:
            timestamps.append({
                "start": round(entry['start'], 2),
                "end": round(entry['start'] + entry['duration'], 2),
                "youtube_text": entry['text'].strip()
            })
        
        return timestamps
        
    except Exception as e:
        print(f"YouTube timestamps unavailable: {e}")
        return None


def transcribe_audio(audio_path, youtube_url=None):
    """
    🔥 HYBRID: Whisper text + YouTube timing
    
    Args:
        audio_path: Path to audio file
        youtube_url: (Optional) YouTube URL for timestamp extraction
    
    Returns:
        dict with 'full_text' and 'timeline'
    """
    
    if not os.path.exists(audio_path):
        raise ValueError("Audio file not found")

    if os.path.getsize(audio_path) < 10000:
        raise ValueError("Audio file too small")

    # Step 1: Transcribe with Whisper (quality text)
    print("📝 Transcribing with Whisper...")
    result = model.transcribe(
        audio_path,
        fp16=False,
        language="en",
        verbose=False,
        condition_on_previous_text=False
    )

    text = result.get("text", "").strip()

    if not text:
        raise ValueError("No speech detected")

    # Step 2: Try to get YouTube timestamps
    if youtube_url:
        print("⏰ Getting YouTube timestamps...")
        youtube_timestamps = get_youtube_timestamps(youtube_url)
        
        if youtube_timestamps:
            print("✅ Using Whisper text + YouTube timing")
            timeline = align_whisper_to_youtube(result, youtube_timestamps)
            
            return {
                "full_text": text,
                "timeline": timeline,
                "source": "hybrid"
            }
    
    # Fallback: Use Whisper segments
    print("⚠️ Using Whisper-only timing")
    segments = result.get("segments", [])
    
    timeline = []
    for seg in segments:
        seg_text = seg["text"].strip()
        if seg_text:
            timeline.append({
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg_text
            })

    return {
        "full_text": text,
        "timeline": timeline,
        "source": "whisper_only"
    }


def align_whisper_to_youtube(whisper_result, youtube_timestamps):
    """
    Align Whisper text to YouTube timing
    Uses YouTube's perfect timestamps with Whisper's better text
    """
    
    whisper_segments = whisper_result.get("segments", [])
    timeline = []
    
    for yt_time in youtube_timestamps:
        yt_start = yt_time["start"]
        yt_end = yt_time["end"]
        
        # Find overlapping Whisper segments
        matching_text = []
        
        for seg in whisper_segments:
            seg_start = seg["start"]
            seg_end = seg["end"]
            
            # Check overlap
            if (seg_start <= yt_end and seg_end >= yt_start):
                matching_text.append(seg["text"].strip())
        
        # Combine or use YouTube text as fallback
        if matching_text:
            combined_text = " ".join(matching_text)
        else:
            combined_text = yt_time["youtube_text"]
        
        # Clean up
        combined_text = combined_text.replace('\n', ' ')
        combined_text = re.sub(r'\s+', ' ', combined_text)
        
        if combined_text.strip():
            timeline.append({
                "start": yt_start,
                "end": yt_end,
                "text": combined_text.strip()
            })
    
    return timeline