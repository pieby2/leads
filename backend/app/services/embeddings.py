from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class EmbeddingClient:
    def __init__(self, api_key: str = None, model: str = None):
        settings = get_settings()
        self.client = genai.Client(api_key=api_key or settings.gemini_api_key)
        self.model = model or settings.embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Batch embed a list of texts. Handles rate limits with retries."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            batch_embeddings = [item.values for item in resp.embeddings]
            all_embeddings.extend(batch_embeddings)

        logger.info("embedded texts with gemini", count=len(texts))
        return all_embeddings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        resp = self.client.models.embed_content(
            model=self.model,
            contents=[text],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return resp.embeddings[0].values
