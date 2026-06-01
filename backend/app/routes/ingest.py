import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import get_settings
from app.database import get_db
from app.db.models import Session, Video, User
from app.models import IngestRequest, IngestResponse, VideoSummary, ErrorResponse
from app.services.youtube import YouTubeService
from app.services.instagram import InstagramService
from app.services.transcription import TranscriptionService
from app.services.chunking import chunk_transcript, compute_engagement_rate
from app.services.embeddings import EmbeddingClient
from app.services.vector_store import VectorStoreService
from app.core.auth import get_current_user

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingest"])

settings = get_settings()

transcription_service = TranscriptionService()
embedder = EmbeddingClient()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_videos(
    req: IngestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a YouTube video (A) and an Instagram reel (B) for comparison."""
    
    # Check usage limits
    limit = 100 if current_user.tier == "free" else 1000
    if current_user.usage_this_month >= limit:
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error_code="USAGE_LIMIT_EXCEEDED",
                message=f"Usage limit exceeded. Upgrade to Pro for more usage."
            ).model_dump(),
        )

    session_id = str(uuid.uuid4())

    try:
        # increment usage
        current_user.usage_this_month += 1
        db.add(current_user)

        # create session record
        session = Session(
            id=session_id,
            user_id=current_user.id,
            youtube_url=str(req.youtube_url),
            instagram_url=str(req.instagram_url) if req.instagram_url else "",
            status="processing",
        )
        db.add(session)
        await db.flush()

        videos_response = {}

        videos_to_process = [("A", str(req.youtube_url), "youtube")]
        if req.instagram_url:
            videos_to_process.append(("B", str(req.instagram_url), "instagram"))

        # process each video
        for video_id, url, platform in videos_to_process:
            url_str = str(url)

            # check cache ?" if we already ingested this URL, reuse metadata
            cached = await _check_cache(db, url_str)
            if cached:
                logger.info("cache hit", url=url_str, video_id=video_id)
                meta = _video_to_meta(cached)
                transcript = cached.transcript_json or []
            else:
                yt_service = YouTubeService(current_user.youtube_access_token)
                ig_service = InstagramService(current_user.instagram_access_token)
                
                # fetch fresh metadata + transcript
                if platform == "youtube":
                    meta = await yt_service.fetch_metadata(url_str)
                    transcript = yt_service.fetch_transcript(url_str)
                else:
                    meta = await ig_service.fetch_metadata(url_str)
                    transcript = ig_service.fetch_transcript(url_str)

                # whisper fallback if no transcript
                if not transcript:
                    logger.info("no transcript, trying whisper", video_id=video_id)
                    transcript = transcription_service.transcribe_from_url(url_str)

            # compute engagement
            engagement = compute_engagement_rate(
                meta.get("views"), meta.get("likes"), meta.get("comments")
            )
            meta["engagement_rate"] = engagement

            # chunk the transcript
            chunks = chunk_transcript(
                transcript,
                chunk_size=settings.chunk_size,
                overlap_tokens=settings.chunk_overlap,
            )

            # embed and store chunks (only if we have them)
            if chunks:
                try:
                    texts = [c["text"] for c in chunks]
                    embeddings = embedder.embed_texts(texts)
                    VectorStoreService(settings.qdrant_host, settings.qdrant_port).upsert_chunks(
                        session_id=session_id,
                        video_id=video_id,
                        chunks=chunks,
                        embeddings=embeddings,
                        metadata={"platform": platform, "source_url": url_str},
                    )
                except Exception as e:
                    logger.error("failed to embed or store chunks", error=str(e), video_id=video_id)

            # save to DB
            video_record = Video(
                session_id=session_id,
                user_id=current_user.id,
                video_id=video_id,
                source_url=url_str,
                platform=platform,
                title=meta.get("title"),
                creator_name=meta.get("creator"),
                views=meta.get("views"),
                likes=meta.get("likes"),
                comments_count=meta.get("comments"),
                duration_sec=meta.get("duration_sec"),
                engagement_rate=engagement,
                thumbnail_url=meta.get("thumbnail_url"),
                upload_date=meta.get("upload_date"),
                follower_count=meta.get("follower_count"),
                hashtags=meta.get("hashtags", []),
                transcript_json=transcript,
            )
            db.add(video_record)

            videos_response[video_id] = VideoSummary(
                title=meta.get("title"),
                creator=meta.get("creator"),
                platform=platform,
                views=meta.get("views"),
                likes=meta.get("likes"),
                comments=meta.get("comments"),
                duration_sec=meta.get("duration_sec"),
                engagement_rate=engagement,
                thumbnail_url=meta.get("thumbnail_url"),
                upload_date=meta.get("upload_date"),
                follower_count=meta.get("follower_count"),
                hashtags=meta.get("hashtags", []),
            )

        # mark session ready
        session.status = "ready"
        await db.flush()

        logger.info("ingestion complete", session_id=session_id)
        return IngestResponse(session_id=session_id, videos=videos_response)

    except Exception as e:
        logger.error("ingestion failed", error=str(e), session_id=session_id)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INGESTION_FAILED",
                message=f"Failed to ingest videos: {str(e)}",
            ).model_dump(),
        )


async def _check_cache(db: AsyncSession, source_url: str) -> Video | None:
    """Check if we've already ingested this URL before."""
    result = await db.execute(
        select(Video).where(Video.source_url == source_url).limit(1)
    )
    return result.scalar_one_or_none()


def _video_to_meta(video: Video) -> dict:
    """Convert a cached Video record back to a metadata dict."""
    return {
        "title": video.title,
        "creator": video.creator_name,
        "views": video.views,
        "likes": video.likes,
        "comments": video.comments_count,
        "duration_sec": video.duration_sec,
        "engagement_rate": video.engagement_rate,
        "thumbnail_url": video.thumbnail_url,
        "upload_date": video.upload_date,
        "platform": video.platform,
        "follower_count": video.follower_count,
        "hashtags": video.hashtags or [],
    }
