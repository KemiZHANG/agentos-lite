# Database Schema

SQLite tables:

- `conversations`, `messages`
- `documents`, `document_chunks`
- `memories`
- `tools`, `tool_calls`
- `approval_requests`
- `agent_runs`, `model_calls`, `retrieval_logs`
- `code_repositories`, `code_files`, `code_symbols`
- `scheduled_tasks`
- `prompt_templates`

Production PostgreSQL + pgvector preparation lives in `backend/app/db/database.py` as `POSTGRES_PGVECTOR_SCHEMA` and is exposed through `/settings/postgres-schema`.

