import re

import yt_dlp
import structlog

logger = structlog.get_logger(__name__)


# TODO: IG scraping is notoriously fragile — yt-dlp works for public reels
# but may break with login walls or rate limits. Consider adding browser-based
# fallback or accepting manual metadata input from the frontend.


def _extract_hashtags(text: str) -> list[str]:
    """Pull #hashtag tokens from a caption string."""
    if not text:
        return []
    return re.findall(r"#(\w+)", text)


class InstagramService:
    """Handles Instagram reel metadata and caption extraction."""

    _ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    def fetch_metadata(self, url: str) -> dict:
        """Try yt-dlp for IG reel metadata. Returns whatever we can get."""
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(str(url), download=False)

            d = info.get("upload_date") or ""
            upload_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else d

            return {
                "title": info.get("title") or info.get("description", "")[:100],
                "creator": info.get("uploader") or info.get("channel"),
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "comments": info.get("comment_count"),
                "duration_sec": info.get("duration"),
                "upload_date": upload_date,
                "thumbnail_url": info.get("thumbnail"),
                "platform": "instagram",
                "follower_count": info.get("channel_follower_count"),
                "hashtags": _extract_hashtags(info.get("description", "")),
            }
        except Exception as e:
            logger.warning("ig metadata fetch failed — platform is flaky", url=url, error=str(e))
            # return a shell so ingestion doesn't fully break
            return {
                "platform": "instagram",
                "title": None,
                "creator": None,
                "views": None,
                "likes": None,
                "comments": None,
                "duration_sec": None,
                "upload_date": None,
                "thumbnail_url": None,
                "follower_count": None,
                "hashtags": [],
            }

    def fetch_transcript(self, url: str) -> list[dict]:
        """
        IG reels rarely have proper captions/subtitles.
        We try to grab the post caption and return it as a single segment.
        If there's audio, the caller should use the Whisper fallback.
        """
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(str(url), download=False)

            caption = info.get("description") or ""
            if caption.strip():
                logger.info("using ig caption as transcript", length=len(caption))
                return [{"text": caption, "start": 0.0, "duration": info.get("duration", 0)}]

            # no caption text — caller should try whisper
            logger.info("no ig caption found, whisper fallback recommended", url=url)
            return []
        except Exception as e:
            logger.warning("ig transcript extraction failed", error=str(e))
            return []

    def get_audio_url(self, url: str) -> str | None:
        """Get direct audio URL for whisper fallback."""
        try:
            opts = {**self._ydl_opts, "format": "bestaudio/best"}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(str(url), download=False)
                return info.get("url")
        except Exception:
            return None
