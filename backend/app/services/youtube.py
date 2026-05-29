import re
from urllib.parse import urlparse, parse_qs

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
import structlog

logger = structlog.get_logger(__name__)


class YouTubeService:
    """Handles YouTube metadata and transcript fetching."""

    _ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    def extract_video_id(self, url: str) -> str:
        """Pull video ID from various YouTube URL formats."""
        parsed = urlparse(str(url))

        if parsed.hostname in ("youtu.be",):
            return parsed.path.lstrip("/")

        if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [None])[0]
            if parsed.path.startswith(("/embed/", "/v/")):
                return parsed.path.split("/")[2]
            if parsed.path.startswith("/shorts/"):
                return parsed.path.split("/")[2]

        # fallback: try regex
        match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", str(url))
        return match.group(1) if match else None

    def fetch_metadata(self, url: str) -> dict:
        """Grab metadata via yt-dlp. Returns a flat dict."""
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(str(url), download=False)

            d = info.get("upload_date") or ""
            upload_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else d

            return {
                "title": info.get("title"),
                "creator": info.get("channel") or info.get("uploader"),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "comments": info.get("comment_count"),
                "duration_sec": info.get("duration"),
                "upload_date": upload_date,
                "thumbnail_url": info.get("thumbnail"),
                "platform": "youtube",
                "follower_count": info.get("channel_follower_count"),
                "hashtags": info.get("tags", []),
            }
        except Exception as e:
            logger.error("youtube metadata fetch failed", url=url, error=str(e))
            return {"platform": "youtube", "title": None, "creator": None, "follower_count": None, "hashtags": []}

    def fetch_transcript(self, url: str) -> list[dict]:
        """Try youtube-transcript-api first. Returns list of segments."""
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.warning("could not extract video id", url=url)
            return []

        try:
            segments = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("transcript fetched via youtube-transcript-api", video_id=video_id, segments=len(segments))
            return [
                {"text": s["text"], "start": s["start"], "duration": s["duration"]}
                for s in segments
            ]
        except Exception as e:
            logger.warning("youtube-transcript-api failed, will need whisper fallback", video_id=video_id, error=str(e))
            return []
