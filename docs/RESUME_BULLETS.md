# Resume Bullets

## 2-Line Short Version

- Built AgentOS Lite, a local-first AI Agent workspace using Next.js, FastAPI, SQLite, RAG citations, long-term memory, tool execution, human approvals, LLMOps, and codebase intelligence.
- Added zero-cost mock providers plus optional Gemini support, with env-only secrets, fallback logging, and AST/regex-based repository indexing for architecture answers and test suggestions.

## 4-Line Standard Version

- Built a self-hosted AI Agent workspace with a full loop: intent detection, RAG/memory/codebase context retrieval, tool selection, approval gates, cited responses, and LLMOps traces.
- Implemented TXT/Markdown RAG with chunk previews, matched keyword snippets, strict citation mode, retrieval logs, and deterministic mock responses for `$0` local demos.
- Designed a Codebase Intelligence Skill that scans repositories, extracts Python AST and TypeScript/JavaScript symbols, explains architecture, locates relevant files, and generates concrete test suggestions.
- Added optional Gemini provider configuration with safe `.env` loading, manual provider health checks, no secret exposure, mock fallback, and demo-limit fallback reasons.

## Technical Keywords Version

Next.js, TypeScript, Tailwind CSS, FastAPI, Pydantic, SQLite, RAG, citations, memory retrieval, tool calling, human-in-the-loop approval, LLMOps, Gemini, mock provider, fallback handling, Python AST, TypeScript parser, codebase intelligence, prompt templates, guardrails.

## Interview Explanation

AgentOS Lite shows how I think about AI products beyond a chat box. A user question becomes an agent run: the backend classifies intent, retrieves the right local context from documents, memory, or indexed code, selects tools, pauses risky actions for approval, generates an answer with citations, and records the whole run in LLMOps. I kept the project zero-cost by default with mock providers, then added optional Gemini support through safe environment configuration and fallback logging.
