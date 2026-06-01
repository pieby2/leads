import asyncio
import re
import httpx
import structlog
from app.config import get_settings

logger = structlog.get_logger(__name__)


class InstagramService:
    """Handles Instagram reel metadata and caption extraction using Apify."""

    def __init__(self, access_token: str | None = None):
        self.settings = get_settings()
        self.apify_token = self.settings.apify_api_token
        self.base_url = "https://api.apify.com/v2"
        self.headers = {"Authorization": f"Bearer {self.apify_token}"} if self.apify_token else {}
        self.access_token = access_token
        self._last_caption = ""
        self._last_duration = 0

    async def _run_actor(self, actor_id: str, input_payload: dict, timeout: int = 120) -> list:
        if not self.apify_token:
            logger.warning("No APIFY_API_TOKEN set, cannot run actor")
            return []

        async with httpx.AsyncClient() as client:
            start_resp = await client.post(
                f"{self.base_url}/acts/{actor_id}/runs",
                headers=self.headers,
                json=input_payload,
                timeout=30,
            )
            start_resp.raise_for_status()
            run_id = start_resp.json()["data"]["id"]
            logger.info("started apify actor", actor_id=actor_id, run_id=run_id)

            deadline = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f"{self.base_url}/actor-runs/{run_id}",
                    headers=self.headers,
                    timeout=10,
                )
                status_resp.raise_for_status()
                status = status_resp.json()["data"]["status"]
                
                if status == "SUCCEEDED":
                    break
                if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    raise RuntimeError(f"Apify actor {actor_id} failed: {status}")

            items_resp = await client.get(
                f"{self.base_url}/actor-runs/{run_id}/dataset/items",
                headers=self.headers,
                params={"format": "json", "clean": "true"},
                timeout=30,
            )
            items_resp.raise_for_status()
            return items_resp.json()

    async def _get_follower_count(self, username: str) -> int | None:
        if not username:
            return None
        try:
            items = await self._run_actor(
                "apify~instagram-profile-scraper",
                {"usernames": [username.lstrip("@")]},
                timeout=60,
            )
            if items:
                return items[0].get("followersCount")
        except Exception as e:
            logger.error("apify profile scrape failed", error=str(e))
        return None

    async def fetch_metadata(self, url: str) -> dict:
        """Fetch metadata via Apify API."""
        try:
            items = await self._run_actor(
                "apify~instagram-reel-scraper",
                {
                    "username": [str(url)],
                    "resultsLimit": 1,
                },
                timeout=120,
            )

            if not items:
                raise ValueError(f"Apify returned no data for URL: {url}")

            item = items[0]
            username = item.get("ownerUsername") or item.get("username")
            follower_count = await self._get_follower_count(username)

            caption = item.get("caption") or item.get("text") or ""
            hashtags = re.findall(r"#\w+", caption)

            def safe_int(v):
                if v is None or v == "": return 0
                try: return int(float(v))
                except (ValueError, TypeError): return 0

            views = safe_int(item.get("videoPlayCount") or item.get("playCount"))
            likes = safe_int(item.get("likesCount") or item.get("likes"))
            comments = safe_int(item.get("commentsCount") or item.get("comments"))

            self._last_caption = caption
            
            raw_duration = item.get("videoDuration") or item.get("duration") or 0.0
            try:
                self._last_duration = float(raw_duration)
            except (ValueError, TypeError):
                self._last_duration = 0.0

            return {
                "platform": "instagram",
                "title": caption[:100].strip() if caption else "Instagram Reel",
                "creator": username,
                "views": views,
                "likes": likes,
                "comments": comments,
                "duration_sec": self._last_duration,
                "upload_date": str(item.get("timestamp") or "")[:10],
                "thumbnail_url": item.get("displayUrl") or item.get("thumbnailUrl"),
                "follower_count": safe_int(follower_count) if follower_count is not None else None,
                "hashtags": hashtags,
            }
        except httpx.HTTPStatusError as e:
            err_text = e.response.text
            logger.error("apify http error", url=url, status=e.response.status_code, body=err_text)
            return {
                "platform": "instagram",
                "title": f"Apify 400: {err_text[:100]}",
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
        except Exception as e:
            logger.error("ig metadata fetch failed", url=url, error=str(e))
            return {
                "platform": "instagram",
                "title": f"Failed: {str(e)[:50]}",
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
        Return the caption we just extracted from the metadata fetch.
        """
        if self._last_caption.strip():
            logger.info("using ig caption as transcript", length=len(self._last_caption))
            return [{"text": self._last_caption, "start": 0.0, "duration": self._last_duration}]

        logger.info("no ig caption found")
        return []

    def get_audio_url(self, url: str) -> str | None:
        """Apify doesn't easily return a direct audio URL, and we don't use yt-dlp anymore."""
        return None
