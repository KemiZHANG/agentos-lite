# Gemini Provider Setup

AgentOS Lite defaults to `LLM_PROVIDER=mock`, so development costs $0 and the app runs with no API keys. Phase 2 supports one real provider: Gemini. Real provider keys are read only from environment variables and must stay in local `.env` files.

Supported values:

- `LLM_PROVIDER=mock`
- `LLM_PROVIDER=gemini`

## Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-local-key
GEMINI_MODEL=gemini-3.1-pro-preview
LLM_FALLBACK_TO_MOCK=true
```

The backend calls the Gemini REST `generateContent` endpoint. If the key or model is invalid and fallback is enabled, the run uses MockLLMProvider and records the provider error plus `fallback_used=true` and a `fallback_reason` in LLMOps.

Environment files are loaded in this priority order:

1. System environment variables
2. `backend/.env`
3. Root `.env`
4. Defaults

`backend/.env` and root `.env` are ignored by Git.

## Provider Health

The Settings page does not call Gemini on page load. Click `Test Provider` to run a manual health check. Mock mode never calls an external API.

The health response reports provider, model, key configured yes/no, status, latency, error, fallback availability, fallback used, and fallback reason. It never returns the API key.

## Demo Mode

For public demos, enable limits:

```env
DEMO_MODE=true
MAX_LLM_CALLS_PER_SESSION=20
MAX_LLM_CALLS_PER_DAY=100
```

When the configured daily limit is exceeded, AgentOS Lite falls back to mock mode and records `fallback_reason=demo_limit`.

## Embeddings

`EMBEDDING_PROVIDER=mock` remains the active default. Phase 2 keeps RAG local with deterministic mock embeddings plus keyword/title matching. Gemini embeddings are not wired into retrieval yet.

## Security

- Never commit `.env`.
- Never paste real keys into README, tests, docs, seed data, or screenshots.
- Settings shows only `llm_api_key_configured=true/false`.
- LLMOps records provider/model/status/error/fallback, never secret values.
