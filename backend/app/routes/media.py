from fastapi import APIRouter, HTTPException, Response
import httpx
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/media", tags=["media"])

@router.get("/proxy-image")
async def proxy_image(url: str):
    """
    Proxies an image from an external URL to bypass browser CORS and hotlinking blocks.
    Specifically used for Instagram CDN thumbnails.
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        async with httpx.AsyncClient() as client:
            # Setting a browser-like user agent sometimes helps with CDN blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            # Add referer if it's an Instagram URL
            if "instagram" in url or "cdninstagram" in url:
                headers["Referer"] = "https://www.instagram.com/"

            response = await client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            response.raise_for_status()

            # Return the raw image bytes with the correct content type
            content_type = response.headers.get("Content-Type", "image/jpeg")
            return Response(content=response.content, media_type=content_type)
            
    except Exception as e:
        logger.error("image proxy failed", url=url, error=str(e))
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {str(e)}")
