# Known Limitations

- Mock LLM responses are deterministic and context-aware for demos, but not as capable as a real provider.
- Mock embeddings are useful for demos but not production-grade semantic search.
- Gemini is the only real LLM provider supported in Phase 2. Tests do not call external APIs, and runtime quality depends on the configured Gemini model.
- Real embedding providers are scaffolded, but Phase 2 RAG still uses local mock embeddings and metadata-aware retrieval.
- PDF support is a clean ingestion stub.
- Authentication is not implemented; the MVP uses `local-user`.
- Scheduler tasks are stored but not executed. APScheduler or Celery beat can be added later.
- PostgreSQL + pgvector schema is prepared but SQLite is the active runtime.
- Codebase TS/JS parsing is regex-based and will miss complex syntax.
- Codebase architecture and test suggestions are deterministic local summaries, not real LLM reasoning yet.
- Large repository indexing is synchronous and should move to background jobs.
- Demo mode has MVP-level call limits; it is a safety guard, not a complete billing or abuse-prevention system.
- Docker Compose is provided for local development convenience, but the documented PowerShell commands are the primary verified local run path.
- Render Free Web Service can cold start after inactivity.
- SQLite on Render Free uses an ephemeral filesystem; hosted demo data and counters can reset after redeploys or restarts.
