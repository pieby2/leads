import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, BigInteger, Float, DateTime, JSON, Text,
    Index, Integer, ForeignKey, Boolean
)

from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tier = Column(String, default="free")
    stripe_customer_id = Column(String, nullable=True)
    usage_this_month = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    youtube_access_token = Column(String, nullable=True)
    youtube_refresh_token = Column(String, nullable=True)
    instagram_access_token = Column(String, nullable=True)
    instagram_user_id = Column(String, nullable=True)

    sessions = relationship("Session", back_populates="user")
    videos = relationship("Video", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    current_period_end = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="subscription")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)  # the session_id we generate
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    youtube_url = Column(String, nullable=False)
    instagram_url = Column(String, nullable=True)
    status = Column(String, default="processing")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
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
    follower_count = Column(BigInteger, nullable=True)
    hashtags = Column(JSON, nullable=True)
    is_cached = Column(Boolean, default=False)

    transcript_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="videos")

    __table_args__ = (
        Index("ix_videos_source_url", "source_url"),
    )
