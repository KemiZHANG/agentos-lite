# Release Notes v0.1

AgentOS Lite v0.1 packages the project for three safe usage modes.

Live demo:

- Frontend: https://agentos-lite-jet.vercel.app
- Backend health: https://agentos-lite-backend.onrender.com/health

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
- Fixed Render build reproducibility with `PYTHON_VERSION=3.12.8`.
- Documented Render cold starts and ephemeral SQLite storage.

## Portfolio Packaging

- README first screen includes Live Demo, Backend Health, local run guide, tech tags, key features, and "not just a chatbot" positioning.
- Added screenshot filename guide, 3-minute demo script, final resume bullets, and GitHub profile setup checklist.

## Safety

- No new model provider.
- No PostgreSQL/pgvector.
- No login system.
- No paid service dependency.
- No real API key in repo.
