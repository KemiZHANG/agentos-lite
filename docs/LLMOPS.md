# LLMOps

The LLMOps dashboard displays:

- Agent runs and trace status.
- Model calls with provider, model, prompt template, estimated input/output tokens, latency, and status.
- Provider errors and `fallback_used` when real providers fall back to MockLLMProvider.
- Retrieval logs with source, query, result count, latency, and results.
- Tool calls with risk level, status, output, and errors.

Token usage is estimated by text length for mock/local fallback. Gemini uses provider usage metadata when it is returned.
