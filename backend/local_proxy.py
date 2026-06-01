#!/usr/bin/env python3
"""
local_proxy.py — Tiny local server that acts as scraping proxy.
Run this ONCE before the demo. Keep it running.

  python backend/local_proxy.py

Then just use the frontend normally — no other commands needed.
"""

import re
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx
import yt_dlp

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YT_AVAILABLE = True
except ImportError:
    YT_AVAILABLE = False

RENDER_BACKEND = "https://vidcompare-backend.onrender.com"
PORT = 8765


def detect_platform(url: str) -> str:
    if "instagram.com" in url or "instagr.am" in url:
        return "instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "unknown"


def extract_yt_id(url: str):
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


def scrape_and_post(url: str, video_id: str) -> dict:
    platform = detect_platform(url)
    print(f"[proxy] Scraping {platform} — {url}")

    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    hashtags = re.findall(r"#\w+", info.get("description") or "")
    segments = []

    if platform == "youtube" and YT_AVAILABLE:
        vid_id = extract_yt_id(url)
        if vid_id:
            try:
                raw = YouTubeTranscriptApi.get_transcript(vid_id)
                segments = [{"text": s["text"], "start": s["start"], "duration": s["duration"]} for s in raw]
            except Exception as e:
                print(f"[proxy] transcript-api failed: {e}")

    elif platform == "instagram":
        caption = info.get("description") or ""
        if caption.strip():
            segments = [{"text": caption, "start": 0.0, "duration": info.get("duration") or 0}]

    payload = {
        "source_url": url,
        "platform": platform,
        "video_id": video_id,
        "title": (info.get("title") or info.get("description", ""))[:100].strip(),
        "creator": info.get("channel") or info.get("uploader"),
        "follower_count": info.get("channel_follower_count"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "comments": info.get("comment_count"),
        "duration_sec": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "thumbnail_url": info.get("thumbnail"),
        "hashtags": hashtags,
        "transcript_segments": segments,
    }

    print(f"[proxy] POSTing to Render backend...")
    resp = httpx.post(
        f"{RENDER_BACKEND}/api/v1/ingest/manual",
        json=payload,
        timeout=90
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"[proxy] Done: {result.get('status')}")
    return result


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logs

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/scrape":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        url = body.get("url")
        video_id = body.get("video_id", "A")

        try:
            result = scrape_and_post(url, video_id)
            self._respond(200, result)
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    print(f"""
╔══════════════════════════════════════════════╗
║   VidCompare Local Proxy — Running on :{PORT}  ║
║   Keep this terminal open during the demo.   ║
║   Just paste URLs in the UI — done!          ║
╚══════════════════════════════════════════════╝
""")
    server = HTTPServer(("localhost", PORT), ProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
