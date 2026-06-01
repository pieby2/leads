import json

from openai import OpenAI
import structlog

from app.config import get_settings
from app.rag.prompts import ROUTER_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


def route_query(state: dict) -> dict:
    """Classify the user query type and target videos using GPT-4o-mini.
    
    Using raw openai client here — langchain is overkill for a simple
    classification call, and mini is way cheaper for routing.
    """
    settings = get_settings()
    client = OpenAI(api_key=state.get("openai_api_key") or settings.openai_api_key)

    user_query = state["user_query"]
    videos = state.get("videos", {})

    # give the model some context about what videos we have
    video_context = ""
    for vid_id, meta in videos.items():
        title = meta.get("title", "Unknown")
        platform = meta.get("platform", "unknown")
        video_context += f"Video {vid_id} ({platform}): {title}\n"

    try:
        resp = client.chat.completions.create(
            model=settings.gpt_mini_model,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Videos:\n{video_context}\n\nQuery: {user_query}"},
            ],
            temperature=0,
            max_tokens=100,
        )

        raw = resp.choices[0].message.content.strip()
        # parse the JSON response
        # strip markdown fences if the model wraps it
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw)
        query_type = parsed.get("query_type", "GENERIC_RAG")
        target_videos = parsed.get("target_videos", ["A", "B"])

        logger.info("query routed", query_type=query_type, targets=target_videos)
        return {"query_type": query_type, "target_videos": target_videos}

    except Exception as e:
        logger.warning("router failed, defaulting to GENERIC_RAG", error=str(e))
        return {"query_type": "GENERIC_RAG", "target_videos": ["A", "B"]}
