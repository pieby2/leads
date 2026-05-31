from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = "sk-your-key-here"
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

    chunk_size: int = 250
    chunk_overlap: int = 30

    gpt_model: str = "gpt-4o-mini"
    gpt_mini_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # vector dimensions for text-embedding-3-small
    embedding_dim: int = 1536
    qdrant_collection: str = "video_chunks"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
