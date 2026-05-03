# Provider Setup

AgentOS Lite defaults to `LLM_PROVIDER=mock`, so it runs with no API keys. Real provider keys are read only from environment variables and must stay in local `.env` files.

## Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-local-key
GEMINI_MODEL=gemini-3.1-pro-preview
LLM_FALLBACK_TO_MOCK=true
```

The backend calls the Gemini REST `generateContent` endpoint. If the key or model is invalid and fallback is enabled, the run uses MockLLMProvider and records the provider error plus `fallback_used=true` in LLMOps.

## DeepSeek

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your-local-key
LLM_MODEL=deepseek-chat
LLM_FALLBACK_TO_MOCK=true
```

## Qwen DashScope International

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=your-local-key
LLM_MODEL=qwen-plus
LLM_FALLBACK_TO_MOCK=true
```

## Ollama Local

Start Ollama with an OpenAI-compatible endpoint, then use:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
LLM_FALLBACK_TO_MOCK=true
```

Use any locally installed Ollama model name.

## Embeddings

`EMBEDDING_PROVIDER=mock` remains the active default. Phase 2 adds provider abstraction and stubs for future `openai_compatible` and `gemini` embeddings, but local RAG still works through deterministic mock embeddings plus keyword/title matching.

## Security

- Never commit `.env`.
- Never paste real keys into README, tests, docs, seed data, or screenshots.
- Settings shows only `llm_api_key_configured=true/false`.
- LLMOps records provider/model/status/error/fallback, never secret values.

