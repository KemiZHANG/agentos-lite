# AgentOS Lite Product Brief

AgentOS Lite is a self-hosted AI workspace for teams that want local control over agent chat, knowledge retrieval, memory, approvals, and observability.

Core modules:

- Web chat workspace with citations, trace steps, and tool calls.
- RAG knowledge base for TXT and Markdown documents.
- Long-term memory for preferences, project context, tool results, and notes.
- Human approval flow for risky tools.
- LLMOps dashboard for agent runs, model calls, retrieval logs, and tool status.
- Codebase intelligence skill for repository questions and test suggestions.

The MVP uses SQLite, MockLLMProvider, and MockEmbeddingProvider so it runs without external services or API keys.

