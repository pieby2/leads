from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database import get_db
from app.db.models import Session, Video
from app.models import VideoSummary, ErrorResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["session"])


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return session metadata and video summaries."""

    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error_code="SESSION_NOT_FOUND",
                message=f"Session {session_id} not found",
            ).model_dump(),
        )

    # fetch videos
    videos_result = await db.execute(
        select(Video).where(Video.session_id == session_id)
    )
    video_records = videos_result.scalars().all()

    videos = {}
    for v in video_records:
        videos[v.video_id] = VideoSummary(
            title=v.title,
            creator=v.creator_name,
            platform=v.platform,
            views=v.views,
            likes=v.likes,
            comments=v.comments_count,
            duration_sec=v.duration_sec,
            engagement_rate=v.engagement_rate,
            thumbnail_url=v.thumbnail_url,
            upload_date=v.upload_date,
            follower_count=v.follower_count,
            hashtags=v.hashtags or [],
        ).model_dump()

    return {
        "session_id": session.id,
        "status": session.status,
        "youtube_url": session.youtube_url,
        "instagram_url": session.instagram_url,
        "created_at": str(session.created_at),
        "videos": videos,
    }
