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

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
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
        }

    def event_stream():
        """SSE generator. Each event is a JSON line."""
        try:
            for token, done, citations in run_rag_graph_stream(
                session_id=req.session_id,
                message=req.message,
                videos_metadata=videos_metadata,
            ):
                if done:
                    data = json.dumps({"token": "", "done": True, "citations": citations or []})
                else:
                    data = json.dumps({"token": token, "done": False})
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error("streaming error", error=str(e))
            error_data = json.dumps({"token": "", "done": True, "error": str(e), "citations": []})
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
