import structlog
from langgraph.graph import StateGraph, END

from app.rag.state import RAGState
from app.rag.nodes.router import route_query
from app.rag.nodes.retriever import retrieve_context
from app.rag.nodes.analyzer import build_analysis
from app.rag.nodes.generator import generate_answer, generate_answer_stream

logger = structlog.get_logger(__name__)

# in-memory session chat histories — good enough for demo, no Redis needed
# TODO: move to Redis or DB if this ever goes beyond single-process demo
_session_memory: dict[str, list[dict]] = {}


def _build_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("route", route_query)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("analyze", build_analysis)
    graph.add_node("generate", generate_answer)

    graph.set_entry_point("route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


# compile once at module level
rag_chain = _build_graph()


def run_rag_graph(
    session_id: str,
    message: str,
    videos_metadata: dict,
    chat_history: list[dict] | None = None,
):
    """Execute the full RAG pipeline (non-streaming). Returns final state."""
    if chat_history is None:
        chat_history = _session_memory.get(session_id, [])

    initial_state: RAGState = {
        "session_id": session_id,
        "videos": videos_metadata,
        "chat_history": chat_history,
        "user_query": message,
        "query_type": "",
        "target_videos": [],
        "retrieved_chunks": [],
        "analysis_context": "",
        "response": "",
        "citations": [],
    }

    result = rag_chain.invoke(initial_state)

    # update session memory
    if session_id not in _session_memory:
        _session_memory[session_id] = []
    _session_memory[session_id].append({"role": "user", "content": message})
    _session_memory[session_id].append({"role": "assistant", "content": result.get("response", "")})

    # keep last 20 messages to avoid token bloat
    if len(_session_memory[session_id]) > 20:
        _session_memory[session_id] = _session_memory[session_id][-20:]

    return result


def run_rag_graph_stream(
    session_id: str,
    message: str,
    videos_metadata: dict,
    chat_history: list[dict] | None = None,
    openai_api_key: str | None = None,
):
    """Execute route + retrieve + analyze, then stream the generation step.
    Yields (token, done, citations) tuples.
    """
    if chat_history is None:
        chat_history = _session_memory.get(session_id, [])

    initial_state: RAGState = {
        "session_id": session_id,
        "videos": videos_metadata,
        "chat_history": chat_history,
        "user_query": message,
        "query_type": "",
        "target_videos": [],
        "retrieved_chunks": [],
        "analysis_context": "",
        "response": "",
        "citations": [],
    }
    if openai_api_key:
        initial_state["openai_api_key"] = openai_api_key

    # run the non-streaming nodes first
    state = dict(initial_state)
    state.update(route_query(state))
    state.update(retrieve_context(state))
    state.update(build_analysis(state))

    # now stream the generation
    full_response = ""
    final_citations = []

    for token, done, citations in generate_answer_stream(state):
        if done:
            final_citations = citations or []
        else:
            full_response += token
        yield token, done, citations

    # update memory after streaming completes
    if session_id not in _session_memory:
        _session_memory[session_id] = []
    _session_memory[session_id].append({"role": "user", "content": message})
    _session_memory[session_id].append({"role": "assistant", "content": full_response})

    if len(_session_memory[session_id]) > 20:
        _session_memory[session_id] = _session_memory[session_id][-20:]
