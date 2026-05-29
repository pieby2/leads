import structlog

logger = structlog.get_logger(__name__)


def chunk_transcript(
    segments: list[dict],
    chunk_size: int = 250,
    overlap_tokens: int = 30,
) -> list[dict]:
    """
    Merge transcript segments into chunks of ~chunk_size tokens.
    Each chunk gets a hook_segment flag if it starts within the first 5 seconds.
    Simple tokenization: split by whitespace.
    """
    if not segments:
        return []

    # flatten all words with their timestamps
    words_with_time = []
    for seg in segments:
        tokens = seg["text"].split()
        seg_start = seg.get("start", 0.0)
        seg_dur = seg.get("duration", 0.0)

        # distribute time evenly across words in segment
        if len(tokens) > 0 and seg_dur > 0:
            time_per_token = seg_dur / len(tokens)
        else:
            time_per_token = 0.0

        for i, token in enumerate(tokens):
            words_with_time.append({
                "word": token,
                "time": seg_start + (i * time_per_token),
            })

    if not words_with_time:
        return []

    chunks = []
    idx = 0
    chunk_index = 0

    while idx < len(words_with_time):
        end_idx = min(idx + chunk_size, len(words_with_time))
        chunk_words = words_with_time[idx:end_idx]

        text = " ".join(w["word"] for w in chunk_words)
        start_sec = chunk_words[0]["time"]
        end_sec = chunk_words[-1]["time"]

        chunks.append({
            "text": text,
            "start_sec": round(start_sec, 2),
            "end_sec": round(end_sec, 2),
            "chunk_index": chunk_index,
            "hook_segment": start_sec < 5.0,
        })

        chunk_index += 1

        # advance by (chunk_size - overlap) to create overlap
        step = max(chunk_size - overlap_tokens, 1)
        idx += step

    logger.info("chunked transcript", total_chunks=len(chunks), total_words=len(words_with_time))
    return chunks


def compute_engagement_rate(views: int | None, likes: int | None, comments: int | None) -> float:
    """Engagement rate = (likes + comments) / views * 100. Returns 0.0 if views is 0 or None."""
    if not views or views == 0:
        return 0.0

    total_interactions = (likes or 0) + (comments or 0)
    return round(total_interactions / views * 100, 4)
