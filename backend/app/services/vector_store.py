import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
import structlog

logger = structlog.get_logger(__name__)


class VectorStoreService:
    _local_client = None

    def __init__(self, host: str = "localhost", port: int = 6333):
        if host == "local":
            if VectorStoreService._local_client is None:
                VectorStoreService._local_client = QdrantClient(path="./qdrant_data")
            self.client = VectorStoreService._local_client
        else:
            self.client = QdrantClient(host=host, port=port)

    def ensure_collection(self, collection_name: str = "video_chunks_v2", vector_size: int = 1536):
        """Create collection if it doesn't exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("created qdrant collection", name=collection_name)
        else:
            logger.info("qdrant collection already exists", name=collection_name)

    def upsert_chunks(
        self,
        session_id: str,
        video_id: str,
        chunks: list[dict],
        embeddings: list[list[float]],
        metadata: dict,
        collection_name: str = "video_chunks_v2",
    ):
        """Insert chunk vectors with metadata into Qdrant."""
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            payload = {
                "session_id": session_id,
                "video_id": video_id,
                "platform": metadata.get("platform", "unknown"),
                "source_url": metadata.get("source_url", ""),
                "chunk_index": chunk["chunk_index"],
                "start_sec": chunk["start_sec"],
                "end_sec": chunk["end_sec"],
                "hook_segment": chunk["hook_segment"],
                "transcript_excerpt": chunk["text"][:200],
                "text": chunk["text"],
            }
            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        # upsert in batches of 64
        batch_size = 64
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=collection_name,
                points=points[i:i + batch_size],
            )

        logger.info("upserted chunks to qdrant", session_id=session_id, video_id=video_id, count=len(points))

    def search(
        self,
        query_embedding: list[float],
        session_id: str,
        video_id: str | None = None,
        hook_only: bool = False,
        top_k: int = 5,
        collection_name: str = "video_chunks_v2",
    ) -> list[dict]:
        """Search for relevant chunks, filtered by session and optionally video/hook."""
        must_filters = [
            FieldCondition(key="session_id", match=MatchValue(value=session_id)),
        ]
        if video_id:
            must_filters.append(
                FieldCondition(key="video_id", match=MatchValue(value=video_id))
            )
        if hook_only:
            must_filters.append(
                FieldCondition(key="hook_segment", match=MatchValue(value=True))
            )

        results = self.client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            query_filter=Filter(must=must_filters),
            limit=top_k,
        )

        hits = []
        for point in results.points:
            hits.append({
                "id": point.id,
                "score": point.score,
                **point.payload,
            })

        return hits

    def delete_session(self, session_id: str, collection_name: str = "video_chunks_v2"):
        """Remove all chunks belonging to a session."""
        self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
        )
        logger.info("deleted session from qdrant", session_id=session_id)
