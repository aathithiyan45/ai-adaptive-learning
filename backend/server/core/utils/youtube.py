import subprocess
import uuid
import os

def download_audio(youtube_url):
    file_id = str(uuid.uuid4())
    output_template = f"/tmp/{file_id}.%(ext)s"
    final_path = f"/tmp/{file_id}.mp3"

    command = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "192K",

        # 🔥 Anti-403 fixes
        "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "--referer", "https://www.youtube.com/",
        "--force-ipv4",
        "--no-playlist",

        "-o", output_template,
        youtube_url
    ]

    subprocess.run(command, check=True)

    if not os.path.exists(final_path) or os.path.getsize(final_path) < 20_000:
        raise ValueError("Downloaded audio is invalid")

    return final_path
