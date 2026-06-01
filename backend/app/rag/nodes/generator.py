import re
from typing import AsyncGenerator

from openai import OpenAI
import structlog

from app.config import get_settings
from app.rag.prompts import RAG_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)

# regex to find citation patterns like [A:chunk_3] or [B:chunk_12]
CITATION_PATTERN = re.compile(r'\[([AB]):chunk_(\d+)\]')


def generate_answer(state: dict) -> dict:
    """Build final prompt and call GPT-4o. Returns full response (non-streaming).
    For streaming, use generate_answer_stream instead.
    """
    settings = get_settings()
    client = OpenAI(api_key=state.get("openai_api_key") or settings.openai_api_key)

    messages = _build_messages(state)

    resp = client.chat.completions.create(
        model=settings.gpt_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )

    answer = resp.choices[0].message.content
    citations = _extract_citations(answer)

    return {"response": answer, "citations": citations}


def generate_answer_stream(state: dict):
    """Streaming version — yields tokens as they come in.
    Returns a generator of (token, is_done, citations) tuples.
    """
    settings = get_settings()
    client = OpenAI(api_key=state.get("openai_api_key") or settings.openai_api_key)

    messages = _build_messages(state)

    stream = client.chat.completions.create(
        model=settings.gpt_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            token = delta.content
            full_response += token
            yield token, False, None

    # final yield with citations
    citations = _extract_citations(full_response)
    yield "", True, citations


def _build_messages(state: dict) -> list[dict]:
    """Assemble the message list for the chat completion."""
    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]

    # add analysis context as a system-ish message
    analysis = state.get("analysis_context", "")
    if analysis:
        messages.append({
            "role": "system",
            "content": f"Here is the analysis context:\n\n{analysis}",
        })

    # replay chat history
    for msg in state.get("chat_history", []):
        messages.append({"role": msg["role"], "content": msg["content"]})

    # current user query
    messages.append({"role": "user", "content": state["user_query"]})

    return messages


def _extract_citations(text: str) -> list[dict]:
    """Pull out citation references from the generated text."""
    matches = CITATION_PATTERN.findall(text)
    citations = []
    seen = set()
    for video_id, chunk_idx in matches:
        key = f"{video_id}:{chunk_idx}"
        if key not in seen:
            citations.append({"video_id": video_id, "chunk_index": int(chunk_idx)})
            seen.add(key)
    return citations
