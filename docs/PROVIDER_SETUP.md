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

The backend calls the Gemini REST `generateContent` endpoint. If the key or model is invalid and fallback is enabled, the run uses MockLLMProvider and records the provider error plus `fallback_used=true` in LLMOps.

## Embeddings

`EMBEDDING_PROVIDER=mock` remains the active default. Phase 2 keeps RAG local with deterministic mock embeddings plus keyword/title matching. Gemini embeddings are not wired into retrieval yet.

## Security

- Never commit `.env`.
- Never paste real keys into README, tests, docs, seed data, or screenshots.
- Settings shows only `llm_api_key_configured=true/false`.
- LLMOps records provider/model/status/error/fallback, never secret values.
