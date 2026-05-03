# Release Notes v0.1

AgentOS Lite v0.1 packages the project for three safe usage modes.

## Local Mock Mode

- Default zero-cost mode.
- No API key required.
- Full demo flow works with MockLLMProvider and MockEmbeddingProvider.

## Local Gemini Mode

- Optional real model mode.
- Users add their own Gemini key in `backend/.env`.
- Settings shows key configured yes/no and never displays the secret.
- Mock fallback remains available.

## Hosted Demo Mode

- Recommended zero-cost portfolio deployment: Vercel frontend + Render FastAPI backend.
- Backend uses Gemini with `DEMO_MODE=true`.
- Each anonymous session gets 5 real Gemini calls per UTC day.
- After the limit, the backend skips Gemini and uses mock fallback.
- LLMOps records `fallback_reason=demo_daily_limit`.

## Deployment Docs

- Added Vercel/Render deployment guide.
- Added Render Blueprint with secret placeholders only.
- Documented Render cold starts and ephemeral SQLite storage.

## Safety

- No new model provider.
- No PostgreSQL/pgvector.
- No login system.
- No paid service dependency.
- No real API key in repo.
