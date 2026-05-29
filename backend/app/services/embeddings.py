from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class EmbeddingClient:
    def __init__(self, api_key: str = None, model: str = None):
        settings = get_settings()
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Batch embed a list of texts. Handles rate limits with retries."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = self.client.embeddings.create(input=batch, model=self.model)
            batch_embeddings = [item.embedding for item in resp.data]
            all_embeddings.extend(batch_embeddings)

        logger.info("embedded texts", count=len(texts))
        return all_embeddings

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        resp = self.client.embeddings.create(input=[text], model=self.model)
        return resp.data[0].embedding
