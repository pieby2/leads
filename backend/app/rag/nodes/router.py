import json

from google import genai
from google.genai import types
import structlog

from app.config import get_settings
from app.rag.prompts import ROUTER_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


def route_query(state: dict) -> dict:
    """Classify the user query type and target videos using Gemini 1.5 Flash."""
    settings = get_settings()
    client = genai.Client(api_key=state.get("gemini_api_key") or settings.gemini_api_key)

    user_query = state["user_query"]
    videos = state.get("videos", {})

    # give the model some context about what videos we have
    video_context = ""
    for vid_id, meta in videos.items():
        title = meta.get("title", "Unknown")
        platform = meta.get("platform", "unknown")
        video_context += f"Video {vid_id} ({platform}): {title}\n"

    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=[{"role": "user", "parts": [{"text": f"Videos:\n{video_context}\n\nQuery: {user_query}"}]}],
            config=types.GenerateContentConfig(
                system_instruction=ROUTER_SYSTEM_PROMPT,
                temperature=0,
                max_output_tokens=100,
                response_mime_type="application/json",
            )
        )

        raw = resp.text.strip()
        parsed = json.loads(raw)
        query_type = parsed.get("query_type", "GENERIC_RAG")
        target_videos = parsed.get("target_videos", ["A", "B"])

        logger.info("query routed", query_type=query_type, targets=target_videos)
        return {"query_type": query_type, "target_videos": target_videos}

    except Exception as e:
        logger.warning("router failed, defaulting to GENERIC_RAG", error=str(e))
        return {"query_type": "GENERIC_RAG", "target_videos": ["A", "B"]}
