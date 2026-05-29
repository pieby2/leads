import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, BigInteger, Float, DateTime, JSON, Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)  # the session_id we generate
    youtube_url = Column(String, nullable=False)
    instagram_url = Column(String, nullable=False)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    video_id = Column(String, nullable=False)  # 'A' or 'B'
    source_url = Column(String, nullable=False)
    platform = Column(String, nullable=False)

    title = Column(String, nullable=True)
    creator_name = Column(String, nullable=True)
    views = Column(BigInteger, nullable=True)
    likes = Column(BigInteger, nullable=True)
    comments_count = Column(BigInteger, nullable=True)
    duration_sec = Column(Float, nullable=True)
    engagement_rate = Column(Float, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    upload_date = Column(String, nullable=True)

    transcript_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_videos_source_url", "source_url"),
    )
