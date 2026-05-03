# LLMOps

The LLMOps dashboard displays:

- Agent runs and trace status.
- Model calls with provider, model, prompt template, estimated input/output tokens, latency, and status.
- Provider errors and `fallback_used` when real providers fall back to MockLLMProvider.
- Fallback reason values such as `missing_key`, `provider_error`, `demo_limit`, or `manual_mock`.
- Retrieval logs with source, query, result count, latency, and results.
- Tool calls with risk level, status, output, and errors.

Token usage is estimated by text length for mock/local fallback. Gemini uses provider usage metadata when it is returned.

Mock provider latency is displayed as `local mock` or `<1ms` in the UI so the dashboard does not imply a real network call. Gemini mode shows measured latency, provider errors, and fallback reason without exposing secrets.
