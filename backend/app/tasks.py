import asyncio
import json
import redis
import structlog
import tenacity
from datetime import datetime

from app.config import get_settings
from app.database import async_session_maker
from app.db.models import Session, Video, User
from app.services.youtube import YouTubeService
from app.services.instagram import InstagramService
from app.services.transcription import TranscriptionService
from app.services.chunking import chunk_transcript, compute_engagement_rate
from app.services.embeddings import EmbeddingClient
from app.services.vector_store import VectorStoreService
from sqlalchemy import select

logger = structlog.get_logger(__name__)
settings = get_settings()
redis_client = redis.from_url(settings.redis_url)

def publish_progress(session_id: str, step: str, progress: int, status: str = "processing"):
    redis_client.publish(
        f"session_progress:{session_id}",
        json.dumps({"step": step, "progress": progress, "status": status})
    )

async def async_process_ingestion(session_id: str, user_id: str, req_data: dict, api_key: str):
    publish_progress(session_id, "Starting processing", 0)
    
    transcription_service = TranscriptionService(api_key=api_key)
    embedder = EmbeddingClient(api_key=api_key)

    try:
        async with async_session_maker() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if not session:
                logger.error("Session not found", session_id=session_id)
                return

            result_user = await db.execute(select(User).where(User.id == user_id))
            current_user = result_user.scalar_one_or_none()

            videos_to_process = [("A", str(req_data["youtube_url"]), "youtube")]
            if req_data.get("instagram_url"):
                videos_to_process.append(("B", str(req_data["instagram_url"]), "instagram"))

            total_videos = len(videos_to_process)
            
            for index, (video_id, url_str, platform) in enumerate(videos_to_process):
                progress_base = int((index / total_videos) * 100)
                publish_progress(session_id, f"Fetching {platform} metadata", progress_base + 5)
                
                # Check cache
                cached_result = await db.execute(select(Video).where(Video.source_url == url_str).limit(1))
                cached = cached_result.scalar_one_or_none()
                
                is_cached = False

                if cached:
                    logger.info("cache hit", url=url_str, video_id=video_id)
                    is_cached = True
                    meta = {
                        "title": cached.title,
                        "creator": cached.creator_name,
                        "views": cached.views,
                        "likes": cached.likes,
                        "comments": cached.comments_count,
                        "duration_sec": cached.duration_sec,
                        "engagement_rate": cached.engagement_rate,
                        "thumbnail_url": cached.thumbnail_url,
                        "upload_date": cached.upload_date,
                        "platform": cached.platform,
                        "follower_count": cached.follower_count,
                        "hashtags": cached.hashtags or [],
                    }
                    transcript = cached.transcript_json or []
                    engagement = cached.engagement_rate
                    # Deduplication: do not re-embed or re-upsert to Qdrant.
                    publish_progress(session_id, f"Loaded {platform} from cache", progress_base + 30)
                else:
                    yt_token = req_data.get("youtube_access_token") or (current_user.youtube_access_token if current_user else None)
                    yt_service = YouTubeService(access_token=yt_token)
                    
                    ig_token = current_user.instagram_access_token if current_user else None
                    ig_service = InstagramService(access_token=ig_token)
                    
                    if platform == "youtube":
                        meta = await yt_service.fetch_metadata(url_str)
                        transcript = yt_service.fetch_transcript(url_str)
                    else:
                        meta = await ig_service.fetch_metadata(url_str)
                        transcript = ig_service.fetch_transcript(url_str)

                    publish_progress(session_id, f"Transcribing {platform}", progress_base + 15)
                    if not transcript:
                        transcript = transcription_service.transcribe_from_url(url_str)

                    engagement = compute_engagement_rate(
                        meta.get("views"), meta.get("likes"), meta.get("comments")
                    )
                    meta["engagement_rate"] = engagement

                    publish_progress(session_id, f"Processing {platform} AI embeddings", progress_base + 30)
                    chunks = chunk_transcript(
                        transcript,
                        chunk_size=settings.chunk_size,
                        overlap_tokens=settings.chunk_overlap,
                    )

                    if chunks:
                        texts = [c["text"] for c in chunks]
                        embeddings = embedder.embed_texts(texts)
                        VectorStoreService(settings.qdrant_host, settings.qdrant_port).upsert_chunks(
                            session_id=session_id,
                            video_id=video_id,
                            chunks=chunks,
                            embeddings=embeddings,
                            metadata={"platform": platform, "source_url": url_str},
                        )

                publish_progress(session_id, f"Saving {platform} record", progress_base + 45)
                
                video_record = Video(
                    session_id=session_id,
                    user_id=user_id,
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
                    is_cached=is_cached,
                )
                db.add(video_record)
                await db.flush()

            session.status = "ready"
            await db.commit()
            
            publish_progress(session_id, "Complete", 100, status="ready")
            logger.info("ingestion complete", session_id=session_id)

    except Exception as e:
        err_msg = str(e)
        if isinstance(e, tenacity.RetryError):
            underlying = e.last_attempt.exception()
            err_msg = f"Failed after retries: {str(underlying)}"
            if "429" in str(underlying):
                err_msg = "Google Gemini Rate Limit Exceeded: Please check your billing dashboard or try again later."

        logger.error("ingestion failed", error=err_msg, session_id=session_id)
        
        async with async_session_maker() as db:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if session:
                session.status = "error"
                await db.commit()
                
        publish_progress(session_id, err_msg, 100, status="error")

def process_ingestion_job(session_id: str, user_id: str, req_data: dict, api_key: str):
    asyncio.run(async_process_ingestion(session_id, user_id, req_data, api_key))
