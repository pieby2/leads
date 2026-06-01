import os
import tempfile

import yt_dlp
from google import genai
from google.genai import types
import structlog
import json

from app.config import get_settings

logger = structlog.get_logger(__name__)


class TranscriptionService:
    """Gemini API fallback when native transcripts aren't available."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.client = genai.Client(api_key=api_key or settings.gemini_api_key)

    def transcribe_from_url(self, source_url: str) -> list[dict]:
        """Download audio via yt-dlp, send to Gemini API, return segments."""
        tmp_path = None
        gemini_file = None
        try:
            # download audio to a temp file
            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, "audio.mp3")

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "outtmpl": tmp_path.replace(".mp3", ".%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([str(source_url)])

            # find the actual file (extension might differ)
            actual_file = tmp_path
            if not os.path.exists(actual_file):
                # look for any audio file in tmp_dir
                for f in os.listdir(tmp_dir):
                    actual_file = os.path.join(tmp_dir, f)
                    break

            logger.info("audio downloaded, uploading to gemini", path=actual_file)

            gemini_file = self.client.files.upload(file=actual_file)
            
            prompt = "Transcribe the audio. Return the transcript as a JSON array of objects, where each object has 'text' (string), 'start' (float in seconds), and 'duration' (float in seconds)."
            
            result = self.client.models.generate_content(
                model=get_settings().gemini_model,
                contents=[gemini_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )

            raw = result.text.strip()
            segments = json.loads(raw)

            logger.info("gemini transcription complete", segments=len(segments))
            return segments

        except Exception as e:
            logger.error("gemini transcription failed", error=str(e))
            return []

        finally:
            # cleanup temp files
            if tmp_path and os.path.exists(tmp_path):
                try:
                    import shutil
                    shutil.rmtree(os.path.dirname(tmp_path), ignore_errors=True)
                except Exception:
                    pass
