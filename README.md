# VidCompare — AI-Powered Video Comparison & Analysis

Compare YouTube videos and Instagram Reels side-by-side with AI-powered insights. Drop in two URLs, get engagement metrics, hook analysis, and actionable growth recommendations through an interactive RAG chatbot.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple)

---

## What It Does

1. **Paste two URLs** — one YouTube video, one Instagram Reel
2. **Auto-ingests** transcripts, metadata, and engagement metrics
3. **Ask questions** like:
   - *"Compare engagement rates"*
   - *"Which video has a better hook in the first 5 seconds?"*
   - *"What can creator B learn from creator A?"*
4. **Get streaming AI responses** with citations back to specific video segments

## Architecture

```mermaid
graph LR
    UI["Next.js Frontend"] -->|REST + SSE| API["FastAPI Backend"]
    
    API -->|Metadata| YT["YouTube<br/>(yt-dlp)"]
    API -->|Metadata| IG["Instagram<br/>(Apify)"]
    API -->|Transcripts| YTAPI["youtube-transcript-api"]
    API -->|Fallback| GeminiAudio["Gemini 1.5 Flash (Audio)"]
    
    API -->|Embed| GEM_EMB["Gemini Embeddings"]
    API -->|Store chunks| Qdrant["Qdrant Vector DB"]
    API -->|Store metadata| PG["PostgreSQL"]
    
    API -->|RAG| LG["LangGraph"]
    LG -->|Retrieve| Qdrant
    LG -->|Generate| GEMINI["Gemini 2.5 Flash"]
```

### RAG Pipeline (LangGraph)

```mermaid
graph TD
    Q["User Question"] --> R["Route Query<br/>(Gemini 2.5 Flash)"]
    R -->|ENGAGEMENT| D1["DB Lookup Only"]
    R -->|HOOK| D2["Vector Search<br/>(hook_segment=true)"]
    R -->|GENERIC| D3["Dual Vector Search<br/>(A + B, top_k=5)"]
    D1 --> A["Build Analysis Context"]
    D2 --> A
    D3 --> A
    A --> G["Generate Answer<br/>(Gemini 2.5 Flash, streaming)"]
    G --> Resp["Streamed Response<br/>with Citations"]
```

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Frontend | Next.js 14 (App Router) | SSR, streaming support, TypeScript |
| Backend | FastAPI | Async Python, typed APIs, LangChain ecosystem |
| Orchestration | LangGraph | Stateful graph with conditional routing + memory |
| Vector DB | Qdrant | Fast filtered search, self-hosted, free |
| Database | PostgreSQL | Reliable metadata store, handles concurrency |
| LLM | Gemini 2.5 Flash (answers + routing) | Fast, cheap, and very high quality with massive context window |
| Embeddings | gemini-embedding-2 | Best cost/quality ratio for Google's newest embedding model |
| Transcription | youtube-transcript-api + Gemini 1.5 Flash Audio | Free text first, multimodal fallback for audio transcription |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Google Gemini API key
- Apify API token (for Instagram scraping)

### 1. Clone and configure

```bash
git clone https://github.com/youruser/vidcompare.git
cd vidcompare

# Set up environment
cp .env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY and APIFY_API_TOKEN
```

### 2. Start infrastructure

```bash
# Start Qdrant + Postgres
docker compose up -d qdrant postgres
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and paste two video URLs.

### Docker (full stack)

```bash
docker compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Qdrant:   http://localhost:6333/dashboard
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, lifespan
│   │   ├── config.py            # Pydantic settings
│   │   ├── models.py            # Request/response schemas
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── db/models.py         # ORM models
│   │   ├── services/
│   │   │   ├── youtube.py       # YT metadata + transcripts
│   │   │   ├── instagram.py     # IG metadata + captions
│   │   │   ├── transcription.py # Whisper API fallback
│   │   │   ├── chunking.py      # Text chunking + hook tagging
│   │   │   ├── embeddings.py    # OpenAI embedding client
│   │   │   └── vector_store.py  # Qdrant operations
│   │   ├── rag/
│   │   │   ├── graph.py         # LangGraph definition
│   │   │   ├── state.py         # Graph state schema
│   │   │   ├── prompts.py       # Prompt templates
│   │   │   └── nodes/           # Router, retriever, analyzer, generator
│   │   └── routes/              # API endpoints
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   └── lib/api.ts           # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest` | Ingest two video URLs, returns session ID |
| `POST` | `/api/v1/chat` | Send message, get SSE-streamed response |
| `GET` | `/api/v1/session/{id}` | Get session metadata + video summaries |
| `GET` | `/health` | Health check |

## Key Design Decisions & Trade-offs

### Why Gemini 2.5 Flash for both routing and answers?
Gemini 2.5 Flash is extremely fast and cost-effective, while providing state-of-the-art quality. It simplifies the architecture to use a single highly capable model for both simple routing tasks and complex reasoning.

### Why Qdrant over Pinecone/Chroma?
- **vs Pinecone**: Self-hosted = no per-query costs at scale. At 1M+ queries/day, Pinecone bills add up fast.
- **vs Chroma**: Qdrant has better filtering (crucial for `video_id` and `hook_segment` queries) and is more production-ready.

### Why SSE over WebSockets for chat?
Chat is request-response with streaming — SSE is simpler (no connection management, automatic reconnection, works through proxies). WebSockets add complexity we don't need.

### Why Apify instead of native scraping for Instagram?
Native Instagram scraping is fragile and prone to IP blocks and login walls. Using managed Apify actors (instagram-reel-scraper and instagram-profile-scraper) ensures reliability without the headache of fighting Meta's anti-scraping measures.

### Why Gemini for transcription instead of local Whisper?
GPU hosting costs don't scale. Using Gemini 1.5 Flash's multimodal capabilities for audio transcription is fast, accurate, and cheaper than maintaining GPU instances until you're processing massive volume.

### Caching strategy
Same video URL = same transcript + embeddings. If a viral video gets submitted by 10K users, we ingest once. This is the single biggest cost saver at scale.

## Cost Analysis (at scale)

### 1,000 creators/day

| Component | Usage | Monthly Cost |
|-----------|-------|-------------|
| Embeddings | ~20K chunks/day × 200 tokens | ~$0.08 |
| Gemini 2.5 Flash | 10K turns × ~800 tokens + routing | ~$0.60 |
| Apify | ~1,000 Reels/day | ~$5.00 |
| Gemini Audio | ~200 videos needing fallback × 3 min avg | ~$0.10 |
| Qdrant (self-hosted) | Single node | $0 (infra cost only) |
| **Total API costs** | | **~$37/month** |

### Scaling to 1M creators/day
- Async ingestion queue (Redis + Celery) for throughput
- Qdrant cluster with sharding for vector capacity
- Consider switching to open-source LLM (Llama 3.1 70B) to cap LLM costs
- CDN + edge caching for static session data
- Per-user rate limiting at API gateway

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `APIFY_API_TOKEN` | Yes | — | Apify API token for Instagram |
| `DATABASE_URL` | No | `postgresql+asyncpg://postgres:postgres@localhost:5432/vidcompare` | Postgres connection |
| `QDRANT_HOST` | No | `localhost` | Qdrant hostname |
| `QDRANT_PORT` | No | `6333` | Qdrant port |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Model for generation and routing |
| `EMBEDDING_MODEL` | No | `gemini-embedding-2` | Embedding model |
| `CHUNK_SIZE` | No | `250` | Target tokens per chunk |
| `CHUNK_OVERLAP` | No | `30` | Overlap tokens between chunks |

## License

MIT
