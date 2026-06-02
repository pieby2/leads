import uuid
import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from rq import Queue

from app.config import get_settings
from app.database import get_db
from app.db.models import Session, User
from app.models import IngestRequest, IngestResponse, ErrorResponse
from app.core.auth import get_current_user
from app.tasks import process_ingestion_job

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingest"])

settings = get_settings()
redis_conn = Redis.from_url(settings.redis_url)
q = Queue(connection=redis_conn)

@router.post("/ingest", response_model=IngestResponse)
async def ingest_videos(
    req: IngestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a YouTube video (A) and an Instagram reel (B) for comparison."""
    
    # Check API key early
    api_key = req.gemini_api_key or settings.gemini_api_key
    if not api_key:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="MISSING_API_KEY",
                message="API key must be set when using the Google AI API. Please provide a key or configure the backend."
            ).model_dump(),
        )

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
            status="queued",
        )
        db.add(session)
        await db.commit()

        # Enqueue the background job
        req_data = req.model_dump()
        req_data["youtube_url"] = str(req_data["youtube_url"])
        if req_data.get("instagram_url"):
            req_data["instagram_url"] = str(req_data["instagram_url"])

        q.enqueue(
            process_ingestion_job,
            session_id,
            current_user.id,
            req_data,
            api_key,
            job_timeout=600  # 10 minutes timeout
        )

        logger.info("ingestion queued", session_id=session_id)
        return IngestResponse(session_id=session_id, status="queued")

    except Exception as e:
        logger.error("ingestion queueing failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INGESTION_QUEUE_FAILED",
                message=str(e),
            ).model_dump(),
        )
