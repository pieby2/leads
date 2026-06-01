import os
import tempfile

import yt_dlp
from openai import OpenAI
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class TranscriptionService:
    """Whisper API fallback when native transcripts aren't available."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)

    def transcribe_from_url(self, source_url: str) -> list[dict]:
        """Download audio via yt-dlp, send to Whisper API, return segments."""
        tmp_path = None
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

            logger.info("audio downloaded, sending to whisper", path=actual_file)

            with open(actual_file, "rb") as audio_file:
                result = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            segments = []
            for seg in result.segments:
                segments.append({
                    "text": seg.text.strip(),
                    "start": seg.start,
                    "duration": seg.end - seg.start,
                })

            logger.info("whisper transcription complete", segments=len(segments))
            return segments

        except Exception as e:
            logger.error("whisper transcription failed", error=str(e))
            return []

        finally:
            # cleanup temp files
            if tmp_path and os.path.exists(tmp_path):
                try:
                    import shutil
                    shutil.rmtree(os.path.dirname(tmp_path), ignore_errors=True)
                except Exception:
                    pass
