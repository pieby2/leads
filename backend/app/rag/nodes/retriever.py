import structlog

from app.config import get_settings
from app.services.embeddings import EmbeddingClient
from app.services.vector_store import VectorStoreService

logger = structlog.get_logger(__name__)


def retrieve_context(state: dict) -> dict:
    """Retrieve relevant chunks based on query type and target videos."""
    settings = get_settings()
    query_type = state.get("query_type", "GENERIC_RAG")
    target_videos = state.get("target_videos", ["A", "B"])
    session_id = state["session_id"]
    user_query = state["user_query"]

    # for pure metadata queries, skip vector search entirely
    if query_type in ("ENGAGEMENT_COMPARISON", "CREATOR_INFO"):
        logger.info("skipping vector search for metadata query", query_type=query_type)
        return {"retrieved_chunks": []}

    # embed the query
    embedder = EmbeddingClient(api_key=state.get("gemini_api_key"))
    query_embedding = embedder.embed_query(user_query)

    vs = VectorStoreService(settings.qdrant_host, settings.qdrant_port)

    all_chunks = []
    hook_only = query_type == "HOOK_COMPARISON"
    top_k = 5

    for vid_id in target_videos:
        source_url = state.get("videos", {}).get(vid_id, {}).get("source_url")
        hits = vs.search(
            query_embedding=query_embedding,
            session_id=session_id,
            source_url=source_url,
            video_id=vid_id,
            hook_only=hook_only,
            top_k=top_k,
        )
        for hit in hits:
            all_chunks.append({
                "chunk_id": f"{hit['video_id']}:chunk_{hit['chunk_index']}",
                "video_id": hit["video_id"],
                "chunk_index": hit["chunk_index"],
                "excerpt": hit.get("text", hit.get("transcript_excerpt", "")),
                "start_sec": hit.get("start_sec", 0),
                "end_sec": hit.get("end_sec", 0),
                "score": hit.get("score", 0),
                "hook_segment": hit.get("hook_segment", False),
            })

    logger.info("retrieved chunks", count=len(all_chunks), query_type=query_type)
    return {"retrieved_chunks": all_chunks}
