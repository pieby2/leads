from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = "sk-your-key-here"
    database_url: str = "sqlite+aiosqlite:///./vidcompare.db"

    qdrant_host: str = "local"
    qdrant_port: int = 6333

    chunk_size: int = 250
    chunk_overlap: int = 30

    gpt_model: str = "gpt-4o"
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
