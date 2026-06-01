from typing import TypedDict


class RAGState(TypedDict, total=False):
    session_id: str
    videos: dict          # {'A': {...metadata}, 'B': {...metadata}}
    chat_history: list     # [{'role': 'user'|'assistant', 'content': str}]
    user_query: str
    query_type: str        # ENGAGEMENT_COMPARISON, HOOK_COMPARISON, CREATOR_INFO, IMPROVEMENT_SUGGESTIONS, GENERIC_RAG
    target_videos: list    # ['A'], ['B'], or ['A', 'B']
    retrieved_chunks: list # list of chunk dicts from vector search
    analysis_context: str  # formatted context string for the generator
    response: str          # final generated answer
    citations: list        # [{'video_id': 'A', 'chunk_index': 3}, ...]
    openai_api_key: str    # optional custom API key
