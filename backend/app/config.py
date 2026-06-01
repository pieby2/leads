from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    database_url: str = "sqlite+aiosqlite:///./vidcompare.db"
    redis_url: str = "redis://localhost:6379"

    qdrant_host: str = "local"
    qdrant_port: int = 6333

    # OAuth 2.0 Credentials
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    instagram_client_id: str = ""
    instagram_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/api/auth"

    # Stripe & URLs
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = "price_dummy"
    frontend_url: str = "https://vidcompare-frontend.onrender.com"

    residential_proxy: str | None = None
    apify_api_token: str | None = None

    chunk_size: int = 250
    chunk_overlap: int = 30

    # AI Provider Settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    embedding_model: str = "gemini-embedding-2"

    # vector dimensions for gemini-embedding-2
    embedding_dim: int = 3072
    qdrant_collection: str = "video_chunks_v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
