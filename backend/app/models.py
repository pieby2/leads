from pydantic import BaseModel, HttpUrl
from typing import Optional


class IngestRequest(BaseModel):
    youtube_url: HttpUrl
    instagram_url: Optional[HttpUrl] = None


class VideoSummary(BaseModel):
    title: Optional[str] = None
    creator: Optional[str] = None
    platform: str
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    duration_sec: Optional[float] = None
    engagement_rate: Optional[float] = None
    thumbnail_url: Optional[str] = None
    upload_date: Optional[str] = None
    follower_count: Optional[int] = None
    hashtags: Optional[list[str]] = None


class IngestResponse(BaseModel):
    session_id: str
    videos: dict[str, VideoSummary]  # keys are 'A' and 'B'


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatChunk(BaseModel):
    token: str
    done: bool
    citations: Optional[list[dict]] = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    retry_after: Optional[int] = None
