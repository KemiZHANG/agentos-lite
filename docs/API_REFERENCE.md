# API Reference

Base URL: `http://localhost:8000`

- `GET /health`
- `POST /chat`
- `GET /chat/conversations`
- `GET /chat/conversations/{conversation_id}/messages`
- `GET /documents`
- `POST /documents/upload`
- `GET /documents/search?q=...`
- `GET /memory`, `POST /memory`, `PUT /memory/{id}`, `DELETE /memory/{id}`
- `GET /tools`, `GET /tools/calls`, `POST /tools/call`
- `GET /approvals`, `POST /approvals/{id}/decision`
- `GET /codebase/repositories`, `POST /codebase/index`, `GET /codebase/search`
- `POST /codebase/question`, `POST /codebase/find-files`, `POST /codebase/test-suggestions`
- `GET /llmops`
- `GET /settings`, `GET /settings/prompts`, `POST /settings/prompts`
- `GET /settings/scheduled-tasks`, `POST /settings/scheduled-tasks`, `PUT /settings/scheduled-tasks/{id}`

Errors use `{ "error": { "code": "...", "message": "...", "details": ... } }`.

