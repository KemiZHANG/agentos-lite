# AgentOS Lite Agent Notes

This repository is a local-first MVP. Prefer runnable increments over large rewrites.

Operational defaults:

- Backend: FastAPI with SQLite.
- Frontend: Next.js, TypeScript, Tailwind CSS.
- LLM and embeddings: mock providers by default.
- Auth: default local user `local-user`.
- Guardrails: never execute shell commands from user input, never delete files, never send emails, and require approval for risky tools.

When extending the project, keep docs updated and add focused tests for changed behavior.

