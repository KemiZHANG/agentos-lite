# AgentOS Lite

Self-hosted AI workspace MVP with RAG, memory, codebase intelligence, tool execution, human approvals, scheduler-ready tasks, prompt versioning, and LLMOps monitoring.

The app runs locally without API keys by using `MockLLMProvider` and `MockEmbeddingProvider`.

## Quick Start

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH=".."
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Optional demo seed:

```bash
cd backend
$env:PYTHONPATH=".."
python ..\scripts\seed_demo.py
```

## What Works

- Dashboard-style Next.js UI with pages for overview, chat, documents, memory, tools, approvals, codebase, LLMOps, and settings.
- FastAPI backend with structured error responses and CORS for local frontend development.
- SQLite persistence for conversations, messages, documents, chunks, memories, tools, tool calls, approvals, agent runs, model calls, retrieval logs, code repositories/files/symbols, scheduled tasks, and prompt templates.
- TXT and Markdown document upload, chunking, mock embeddings, local retrieval, and citations.
- Lightweight agent workflow with intent detection, planner, memory retrieval, RAG retrieval, tool selection, answer generation, verification, and final response trace.
- Codebase intelligence using Python `ast` and lightweight TS/JS regex parsing.
- Human approval queue for risky tools.
- LLMOps dashboard with estimated token usage and latency.
- PostgreSQL + pgvector schema preparation in docs and `/settings/postgres-schema`.

## Default Local User

Full auth is intentionally deferred. All data belongs to `local-user` by default.

## Tests

```bash
cd backend
$env:PYTHONPATH=".."
pytest
```

Frontend validation:

```bash
cd frontend
npm run typecheck
npm run build
```

## Demo Flow

1. Start backend and frontend.
2. Upload `examples/sample_docs/product_brief.md`.
3. Go to Codebase Intelligence and click `Index sample repo`.
4. Ask chat: `Which files are related to document upload?`
5. Ask chat: `remember that I prefer concise local MVP decisions`.
6. Open Tools and Approvals, approve the paused memory request.
7. Open LLMOps to see traces, model calls, retrieval logs, and tool calls.

## Production Direction

Replace mock providers with real provider implementations, switch SQLite retrieval to PostgreSQL + pgvector, add authentication, add a background scheduler such as APScheduler or Celery beat, and harden file ingestion for larger repositories and PDFs.

