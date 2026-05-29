from app.services.chunking import chunk_transcript


def test_basic_chunking():
    """Chunks a simple transcript and checks structure."""
    segments = [
        {"text": " ".join(f"word{i}" for i in range(100)), "start": 0.0, "duration": 30.0},
        {"text": " ".join(f"word{i}" for i in range(100, 200)), "start": 30.0, "duration": 30.0},
        {"text": " ".join(f"word{i}" for i in range(200, 350)), "start": 60.0, "duration": 45.0},
    ]

    chunks = chunk_transcript(segments, chunk_size=100, overlap_tokens=10)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "text" in chunk
        assert "start_sec" in chunk
        assert "end_sec" in chunk
        assert "chunk_index" in chunk
        assert "hook_segment" in chunk
        assert chunk["end_sec"] >= chunk["start_sec"]


def test_hook_tagging():
    """First chunk starting at 0s should be tagged as hook."""
    segments = [
        {"text": "hey everyone welcome to my channel", "start": 0.0, "duration": 3.0},
        {"text": "today we are going to talk about something cool", "start": 3.0, "duration": 4.0},
        {"text": "so let me get right into it and show you", "start": 7.0, "duration": 5.0},
    ]

    chunks = chunk_transcript(segments, chunk_size=20, overlap_tokens=3)

    # first chunk should be hook (starts at 0)
    assert chunks[0]["hook_segment"] is True

    # find a chunk that starts after 5s, should not be hook
    non_hook = [c for c in chunks if c["start_sec"] >= 5.0]
    if non_hook:
        assert non_hook[0]["hook_segment"] is False


def test_overlap():
    """Chunks should share some tokens at boundaries."""
    words = " ".join(f"w{i}" for i in range(100))
    segments = [{"text": words, "start": 0.0, "duration": 30.0}]

    chunks = chunk_transcript(segments, chunk_size=30, overlap_tokens=10)

    if len(chunks) >= 2:
        # check that chunks overlap — last words of chunk 0 should appear in chunk 1
        words_0 = set(chunks[0]["text"].split()[-10:])
        words_1 = set(chunks[1]["text"].split()[:10])
        overlap = words_0 & words_1
        assert len(overlap) > 0, "Expected overlap between consecutive chunks"


def test_empty_segments():
    """Empty input should return empty output."""
    assert chunk_transcript([]) == []
    assert chunk_transcript([{"text": "", "start": 0, "duration": 0}]) == []


def test_single_small_segment():
    """A tiny segment should produce exactly one chunk."""
    segments = [{"text": "just a few words", "start": 0.0, "duration": 2.0}]
    chunks = chunk_transcript(segments, chunk_size=250, overlap_tokens=30)
    assert len(chunks) == 1
    assert chunks[0]["hook_segment"] is True
