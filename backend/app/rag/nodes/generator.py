import re
from typing import AsyncGenerator

from google import genai
from google.genai import types
import structlog

from app.config import get_settings
from app.rag.prompts import RAG_SYSTEM_PROMPT

logger = structlog.get_logger(__name__)

# regex to find citation patterns like [A:chunk_3] or [B:chunk_12]
import re
CITATION_PATTERN = re.compile(r'\[([AB]):chunk_(\d+)\]')


def generate_answer(state: dict) -> dict:
    """Build final prompt and call Gemini. Returns full response (non-streaming)."""
    settings = get_settings()
    client = genai.Client(api_key=state.get("gemini_api_key") or settings.gemini_api_key)

    system_instruction, contents = _build_messages(state)

    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1500,
        )
    )

    answer = resp.text
    citations = _extract_citations(answer)

    return {"response": answer, "citations": citations}


def generate_answer_stream(state: dict):
    """Streaming version — yields tokens as they come in.
    Returns a generator of (token, is_done, citations) tuples.
    """
    settings = get_settings()
    client = genai.Client(api_key=state.get("gemini_api_key") or settings.gemini_api_key)

    system_instruction, contents = _build_messages(state)

    stream = client.models.generate_content_stream(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1500,
        )
    )

    full_response = ""
    for chunk in stream:
        if chunk.text:
            token = chunk.text
            full_response += token
            yield token, False, None

    # final yield with citations
    citations = _extract_citations(full_response)
    yield "", True, citations


def _build_messages(state: dict) -> tuple[str, list]:
    """Assemble the system instruction and conversation history for Gemini."""
    system_instruction = RAG_SYSTEM_PROMPT

    # add analysis context to system prompt
    analysis = state.get("analysis_context", "")
    if analysis:
        system_instruction += f"\n\nHere is the analysis context:\n{analysis}"

    contents = []
    # replay chat history
    for msg in state.get("chat_history", []):
        contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

    # current user query
    contents.append({"role": "user", "parts": [{"text": state["user_query"]}]})

    return system_instruction, contents


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
