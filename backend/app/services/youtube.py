import re
from urllib.parse import urlparse, parse_qs

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
import structlog

logger = structlog.get_logger(__name__)


from app.config import get_settings


class YouTubeService:
    """Handles YouTube metadata and transcript fetching."""

    def __init__(self, access_token: str | None = None):
        settings = get_settings()
        self.access_token = access_token
        self._ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if settings.residential_proxy:
            self._ydl_opts["proxy"] = settings.residential_proxy

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

    async def fetch_metadata(self, url: str) -> dict:
        """Grab metadata via official API if authenticated, else fallback to yt-dlp."""
        video_id = self.extract_video_id(url)
        
        if self.access_token and video_id:
            try:
                import httpx
                api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,statistics"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                async with httpx.AsyncClient() as client:
                    resp = await client.get(api_url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("items"):
                            item = data["items"][0]
                            snippet = item.get("snippet", {})
                            stats = item.get("statistics", {})
                            
                            d = snippet.get("publishedAt", "")[:10]
                            
                            thumbnails = snippet.get("thumbnails", {})
                            best_thumb = thumbnails.get("maxres") or thumbnails.get("high") or thumbnails.get("default", {})
                            
                            return {
                                "title": snippet.get("title"),
                                "creator": snippet.get("channelTitle"),
                                "views": int(stats.get("viewCount", 0)),
                                "likes": int(stats.get("likeCount", 0)),
                                "comments": int(stats.get("commentCount", 0)),
                                "duration_sec": None, # Data API requires contentDetails part for duration (PTM format parsing)
                                "upload_date": d,
                                "thumbnail_url": best_thumb.get("url"),
                                "platform": "youtube",
                                "follower_count": None, # Requires another API call to channels
                                "hashtags": snippet.get("tags", []),
                            }
            except Exception as e:
                logger.error("youtube official api fetch failed", url=url, error=str(e))
                # Fall through to yt-dlp

        # Fallback to scraping
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
            logger.error("youtube metadata fetch fallback failed", url=url, error=str(e))
            return {"platform": "youtube", "title": f"Failed to load: {str(e)[:50]}", "creator": None, "follower_count": None, "hashtags": []}

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
