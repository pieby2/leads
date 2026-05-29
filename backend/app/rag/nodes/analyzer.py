import structlog

logger = structlog.get_logger(__name__)


def build_analysis(state: dict) -> dict:
    """Format retrieved chunks and video metadata into a structured context string."""
    videos = state.get("videos", {})
    chunks = state.get("retrieved_chunks", [])
    query_type = state.get("query_type", "GENERIC_RAG")

    parts = []

    # always include metadata summary
    parts.append("=== VIDEO METADATA ===")
    for vid_id in ("A", "B"):
        meta = videos.get(vid_id, {})
        if not meta:
            continue
        parts.append(f"\n--- Video {vid_id} ({meta.get('platform', 'unknown')}) ---")
        parts.append(f"Title: {meta.get('title', 'N/A')}")
        parts.append(f"Creator: {meta.get('creator', 'N/A')}")
        parts.append(f"Views: {_fmt_number(meta.get('views'))}")
        parts.append(f"Likes: {_fmt_number(meta.get('likes'))}")
        parts.append(f"Comments: {_fmt_number(meta.get('comments'))}")
        parts.append(f"Duration: {meta.get('duration_sec', 'N/A')}s")
        parts.append(f"Engagement Rate: {meta.get('engagement_rate', 'N/A')}%")
        parts.append(f"Upload Date: {meta.get('upload_date', 'N/A')}")
        parts.append(f"Follower Count: {_fmt_number(meta.get('follower_count'))}")
        hashtags = meta.get("hashtags") or []
        parts.append(f"Hashtags: {', '.join(hashtags) if hashtags else 'N/A'}")

    # for engagement comparisons, add a quick comparison table
    if query_type == "ENGAGEMENT_COMPARISON" and len(videos) == 2:
        parts.append("\n=== ENGAGEMENT COMPARISON ===")
        a = videos.get("A", {})
        b = videos.get("B", {})
        parts.append(f"{'Metric':<20} {'Video A':>15} {'Video B':>15}")
        parts.append("-" * 52)
        for metric in ("views", "likes", "comments"):
            va = _fmt_number(a.get(metric))
            vb = _fmt_number(b.get(metric))
            parts.append(f"{metric.capitalize():<20} {va:>15} {vb:>15}")
        parts.append(f"{'Engagement Rate':<20} {a.get('engagement_rate', 0):>14.2f}% {b.get('engagement_rate', 0):>14.2f}%")

    # add transcript chunks if we have them
    if chunks:
        parts.append("\n=== RELEVANT TRANSCRIPT EXCERPTS ===")
        for chunk in chunks:
            vid_id = chunk.get("video_id", "?")
            idx = chunk.get("chunk_index", 0)
            excerpt = chunk.get("excerpt", "")
            start = chunk.get("start_sec", 0)
            hook = " [HOOK]" if chunk.get("hook_segment") else ""
            parts.append(f"\n({vid_id}:chunk_{idx}) [{start}s]{hook}:")
            parts.append(excerpt)

    analysis_context = "\n".join(parts)
    logger.info("built analysis context", length=len(analysis_context))
    return {"analysis_context": analysis_context}


def _fmt_number(n) -> str:
    if n is None:
        return "N/A"
    if isinstance(n, (int, float)):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(int(n))
    return str(n)
