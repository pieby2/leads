from pydantic import BaseModel, HttpUrl
from typing import Optional


class IngestRequest(BaseModel):
    youtube_url: HttpUrl
    instagram_url: Optional[HttpUrl] = None


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class ManualIngestRequest(BaseModel):
    source_url: str
    platform: str  # "youtube" or "instagram"
    video_id: str  # "A" or "B" 
    title: Optional[str] = None
    creator: Optional[str] = None
    follower_count: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    duration_sec: Optional[int] = None
    upload_date: Optional[str] = None
    thumbnail_url: Optional[str] = None
    hashtags: Optional[list[str]] = []
    transcript_segments: Optional[list[TranscriptSegment]] = []


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
