import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_db
from app.db.models import Session, Video
from app.models import ChatRequest, ErrorResponse
from app.rag.graph import run_rag_graph_stream
from app.core.auth import get_current_user
from app.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])
settings = get_settings()


@router.post("/chat")
async def chat(
    req: ChatRequest, 
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Stream a RAG-powered chat response for a video comparison session."""

    # validate session exists and is ready
    result = await db.execute(
        select(Session).where(Session.id == req.session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error_code="SESSION_NOT_FOUND",
                message=f"Session {req.session_id} not found",
            ).model_dump(),
        )

    if session.status != "ready":
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="SESSION_NOT_READY",
                message=f"Session is still {session.status}. Please wait.",
            ).model_dump(),
        )

    # load video metadata for this session
    videos_result = await db.execute(
        select(Video).where(Video.session_id == req.session_id)
    )
    video_records = videos_result.scalars().all()

    videos_metadata = {}
    for v in video_records:
        videos_metadata[v.video_id] = {
            "source_url": v.source_url,
            "title": v.title,
            "creator": v.creator_name,
            "platform": v.platform,
            "views": v.views,
            "likes": v.likes,
            "comments": v.comments_count,
            "duration_sec": v.duration_sec,
            "engagement_rate": v.engagement_rate,
            "thumbnail_url": v.thumbnail_url,
            "upload_date": v.upload_date,
            "follower_count": v.follower_count,
            "hashtags": v.hashtags or [],
        }

    def generate_suggested_questions(api_key: str, message: str, answer: str) -> list[str]:
        import google.genai as genai
        try:
            client = genai.Client(api_key=api_key or settings.gemini_api_key)
            prompt = f"Based on the user's last message: '{message}'\nAnd the assistant's answer:\n'{answer}'\n\nGenerate exactly 3 short, smart follow-up questions the user could ask next. Output ONLY a JSON list of 3 strings."
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            # clean json if it contains markdown formatting
            text = response.text.replace('```json', '').replace('```', '').strip()
            questions = json.loads(text)
            return questions[:3]
        except Exception as e:
            logger.error("Failed to generate suggested questions", error=str(e))
            return []

    def event_stream():
        """SSE generator. Each event is a JSON line."""
        try:
            answer_so_far = ""
            for token, done, citations in run_rag_graph_stream(
                session_id=req.session_id,
                message=req.message,
                videos_metadata=videos_metadata,
                gemini_api_key=req.gemini_api_key,
            ):
                if done:
                    suggestions = generate_suggested_questions(req.gemini_api_key, req.message, answer_so_far)
                    data = json.dumps({"token": "", "done": True, "citations": citations or [], "suggested_questions": suggestions})
                else:
                    answer_so_far += token
                    data = json.dumps({"token": token, "done": False})
                yield f"data: {data}\n\n"
        except Exception as e:
            import tenacity
            err_msg = str(e)
            if isinstance(e, tenacity.RetryError):
                underlying = e.last_attempt.exception()
                err_msg = f"Failed after retries: {str(underlying)}"
                if "429" in str(underlying):
                    err_msg = "Google Gemini Rate Limit Exceeded: Please check your billing dashboard or try again later."
                elif "API key not valid" in str(underlying):
                    err_msg = "API key not valid. Please pass a valid Google Gemini API key."
                else:
                    err_msg = str(underlying)
                    
            logger.error("streaming error", error=err_msg)
            error_data = json.dumps({"token": "", "done": True, "error": err_msg, "citations": []})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
