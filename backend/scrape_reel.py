#!/usr/bin/env python3
"""
scrape_reel.py — Run locally (residential IP) to pre-cache videos before demo.
Usage:
  python scrape_reel.py <url> <video_id> [backend_url]

Examples:
  python scrape_reel.py "https://youtu.be/xxxx" A
  python scrape_reel.py "https://www.instagram.com/reels/xxxx/" B
  python scrape_reel.py "https://youtu.be/xxxx" A https://vidcompare-backend.onrender.com
"""

import sys
import json
import httpx
import yt_dlp

# YouTube also uses youtube-transcript-api for captions
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YT_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YT_TRANSCRIPT_AVAILABLE = False

DEFAULT_BACKEND = "https://vidcompare-backend.onrender.com"


def detect_platform(url: str) -> str:
    if "instagram.com" in url or "instagr.am" in url:
        return "instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    raise ValueError(f"Unsupported URL: {url}")


def extract_yt_video_id(url: str) -> str | None:
    import re
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
    match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def scrape_metadata(url: str, platform: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    hashtags = []
    desc = info.get("description") or ""
    import re
    hashtags = re.findall(r"#\w+", desc)

    return {
        "source_url": url,
        "platform": platform,
        "title": (info.get("title") or desc[:100]).strip(),
        "creator": info.get("channel") or info.get("uploader"),
        "follower_count": info.get("channel_follower_count"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "comments": info.get("comment_count"),
        "duration_sec": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "thumbnail_url": info.get("thumbnail"),
        "hashtags": hashtags,
    }


def scrape_transcript(url: str, platform: str, info: dict) -> list[dict]:
    segments = []

    if platform == "youtube" and YT_TRANSCRIPT_AVAILABLE:
        video_id = extract_yt_video_id(url)
        if video_id:
            try:
                raw = YouTubeTranscriptApi.get_transcript(video_id)
                segments = [
                    {"text": s["text"], "start": s["start"], "duration": s["duration"]}
                    for s in raw
                ]
                print(f"  ✅ YouTube transcript: {len(segments)} segments")
                return segments
            except Exception as e:
                print(f"  ⚠️  youtube-transcript-api failed: {e}")

    # Fallback: use caption/description as single segment
    if platform == "instagram":
        caption = info.get("description") or ""
        if caption.strip():
            segments = [{"text": caption, "start": 0.0, "duration": info.get("duration") or 0}]
            print(f"  ℹ️  Using IG caption as transcript ({len(caption)} chars)")
        else:
            print("  ⚠️  No caption found. Consider adding transcript manually.")

    return segments


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    video_id = sys.argv[2].upper()  # "A" or "B"
    backend_url = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BACKEND

    if video_id not in ("A", "B"):
        print("❌ video_id must be A or B")
        sys.exit(1)

    platform = detect_platform(url)
    print(f"\n🔍 Scraping {platform.upper()} video as Video {video_id}...")
    print(f"   URL: {url}")

    # Get metadata
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        raw_info = ydl.extract_info(url, download=False)

    metadata = scrape_metadata(url, platform)
    segments = scrape_transcript(url, platform, raw_info)

    payload = {**metadata, "video_id": video_id, "transcript_segments": segments}

    # Pretty print what we found
    print(f"\n📊 Metadata:")
    print(f"   Title     : {metadata['title']}")
    print(f"   Creator   : {metadata['creator']}")
    print(f"   Followers : {metadata['follower_count']}")
    print(f"   Views     : {metadata['views']}")
    print(f"   Likes     : {metadata['likes']}")
    print(f"   Comments  : {metadata['comments']}")
    print(f"   Hashtags  : {metadata['hashtags']}")
    print(f"   Segments  : {len(segments)}")

    # POST to backend
    endpoint = f"{backend_url.rstrip('/')}/api/v1/ingest/manual"
    print(f"\n📤 POSTing to {endpoint}...")

    try:
        resp = httpx.post(endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        print(f"✅ Success: {result}")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP {e.response.status_code}: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to POST: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
