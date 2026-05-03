# Architecture

AgentOS Lite is a monorepo with a Next.js frontend and FastAPI backend.

- `frontend/` contains the dashboard UI and API client.
- `backend/app/api/` contains HTTP routers.
- `backend/app/services/` contains RAG, memory, tools, approvals, agent orchestration, LLMOps, prompts, scheduler, and codebase intelligence.
- `backend/app/db/database.py` owns the SQLite schema and PostgreSQL + pgvector reference schema.
- `examples/` contains sample documents and a sample repository for demos.

The MVP keeps integrations local. Mock providers make the app useful without external credentials.

## Product Loop

1. The frontend sends a chat request with the current language preference.
2. The backend creates an Agent Run and detects intent.
3. The agent retrieves only the context needed for that intent: documents, memory, or codebase.
4. Tools are selected through the risk policy. Safe tools execute immediately; risky tools create approvals; blocked tools never run.
5. Mock or Gemini generates the answer using assembled prompt context.
6. Guardrails verify citations and confidence.
7. LLMOps records trace steps, model calls, retrieval logs, tool calls, errors, and fallback reason.

## Runtime Choices

- SQLite is the active local database.
- Mock LLM and mock embeddings are the default zero-cost providers.
- Gemini is the only optional real LLM provider in this phase.
- PostgreSQL/pgvector is a later roadmap item, not the active runtime.
