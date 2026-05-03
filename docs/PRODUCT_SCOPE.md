# Product Scope

AgentOS Lite is a local-first AI Agent workspace MVP. The product goal is to make an agent run explainable from input to output:

User question -> context sources -> agent core -> tool execution -> approval when needed -> cited answer -> LLMOps diagnosis.

## In Scope

- Local web workspace for chat, documents, memory, tools, codebase intelligence, LLMOps, and settings.
- SQLite persistence for the MVP.
- Mock LLM and mock embeddings by default for zero-cost development.
- Optional Gemini provider configured only through environment variables.
- TXT/Markdown RAG with chunks, snippets, matched keywords, and citations.
- Long-term memory retrieval for preferences and project context.
- Tool risk policy with safe, approval-required, and blocked tools.
- Codebase indexing for Python/TypeScript/JavaScript plus repo-aware answers and test suggestions.
- LLMOps logs for provider/model/status/latency/tokens/retrieval/tool/fallback data.

## Out of Scope for This Phase

- User authentication and multi-tenant permissions.
- PostgreSQL, pgvector, cloud database, or hosted deployment.
- Paid services by default.
- Additional real providers beyond Gemini.
- Real background scheduler execution.
- Full PDF parsing.
- Shell command execution, file deletion, or email sending.

## Product Principle

Every page should support the same story: AgentOS Lite gathers trusted local context, plans a response, uses tools safely, and leaves an observable trail.
