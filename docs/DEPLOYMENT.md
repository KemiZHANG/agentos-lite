# Deployment Guide

AgentOS Lite supports three usage modes:

- Local mock mode: free, no API key.
- Local Gemini mode: use your own Gemini key in `backend/.env`.
- Hosted demo mode: Vercel frontend + Render FastAPI backend with demo rate limits.

The recommended zero-cost hosted setup is Vercel for `frontend/` and Render Free Web Service for `backend/`.

Reference docs:

- Vercel environment variables: https://vercel.com/docs/environment-variables
- Next.js environment variables: https://nextjs.org/docs/app/guides/environment-variables
- Render web services: https://render.com/docs/web-services
- Render Blueprint spec: https://render.com/docs/blueprint-spec

## Vercel Frontend

1. Import the GitHub repo into Vercel.
2. Set the project root to `frontend`.
3. Use the default Next.js build settings.
4. Set environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-render-backend.onrender.com
```

For local frontend development, use:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

`NEXT_PUBLIC_API_BASE_URL` is intentionally public because it points to the API host, not a secret.

## Render Backend

Create a Render Free Web Service from the same GitHub repo.

Build Command:

```bash
pip install -r backend/requirements.txt
```

Start Command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health Check Path:

```text
/health
```

Render provides the `$PORT` environment variable. The backend must bind to `0.0.0.0`.

## Render Environment Variables

Set these in the Render dashboard:

```env
APP_ENV=production
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.1-pro-preview
LLM_FALLBACK_TO_MOCK=true
DEMO_MODE=true
MAX_LLM_CALLS_PER_USER_PER_DAY=5
DEMO_FALLBACK_TO_MOCK=true
STRICT_CITATION_MODE=true
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Fill `GEMINI_API_KEY` only in the Render dashboard. Do not write a real key in Git, README, docs, tests, screenshots, or logs.

## CORS Setup

`CORS_ORIGINS` must include the deployed Vercel URL. Multiple origins are comma-separated:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-vercel-app.vercel.app
```

The backend enables credentials because hosted demo mode uses an anonymous session cookie.

## Demo Rate Limit

Hosted demo mode uses an anonymous cookie named `agentos_demo_session`.

- Each anonymous session gets `MAX_LLM_CALLS_PER_USER_PER_DAY` real Gemini calls per UTC day.
- Default hosted value: `5`.
- Provider health checks count against this limit if they call Gemini.
- After the limit, the backend does not call Gemini and returns mock fallback with `fallback_reason=demo_daily_limit`.

If cookies are not available, the backend falls back to a hashed IP / `X-Forwarded-For` identity.

## Render Free-Tier Limitations

Render Free Web Services can cold start after inactivity. The first request may be slow while the backend wakes up.

Render Free Web Service filesystem storage is ephemeral. SQLite data may be lost after redeploys, restarts, or instance replacement. This is acceptable for a portfolio demo but not for durable user data.

If long-term hosted persistence is needed later, add a stable database. This v0.1 release intentionally does not add PostgreSQL, pgvector, Redis, or paid services.

## Rotate Gemini Key

1. Open Render dashboard.
2. Replace `GEMINI_API_KEY`.
3. Redeploy or restart the service.
4. Verify Settings -> `Test Provider`.

Never rotate keys through Git commits.

## Disable Gemini

To make hosted demo fully mock-only:

```env
LLM_PROVIDER=mock
DEMO_MODE=false
```

Restart the Render service. The frontend remains unchanged.

## render.yaml

This repo includes `render.yaml` with safe placeholders. It does not contain real secrets. `GEMINI_API_KEY` is marked `sync: false`, so it must be supplied in Render.
