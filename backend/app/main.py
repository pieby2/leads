import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.services.vector_store import VectorStoreService

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up", version="0.1.0")

    # create db tables
    await create_tables()

    # ensure qdrant collection exists
    vs = VectorStoreService(settings.qdrant_host, settings.qdrant_port)
    vs.ensure_collection(settings.qdrant_collection, settings.embedding_dim)

    yield

    logger.info("shutting down")


app = FastAPI(
    title="VidCompare API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — wide open for dev, lock down later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


# mount route modules
from app.routes import ingest, chat, session  # noqa: E402

app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(session.router)
