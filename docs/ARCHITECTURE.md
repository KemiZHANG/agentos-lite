# Architecture

AgentOS Lite is a monorepo with a Next.js frontend and FastAPI backend.

- `frontend/` contains the dashboard UI and API client.
- `backend/app/api/` contains HTTP routers.
- `backend/app/services/` contains RAG, memory, tools, approvals, agent orchestration, LLMOps, prompts, scheduler, and codebase intelligence.
- `backend/app/db/database.py` owns the SQLite schema and PostgreSQL + pgvector reference schema.
- `examples/` contains sample documents and a sample repository for demos.

The MVP keeps integrations local. Mock providers make the app useful without external credentials.

