# Resume Bullets

## English One-Line Version

Built AgentOS Lite, a local-first AI Agent workspace with RAG citations, long-term memory, tool calling, human-in-the-loop approvals, LLMOps, optional Gemini, and AST-based codebase intelligence.

## English Three-Bullet Version

- Built a self-hosted AI Agent workspace with Next.js, FastAPI, SQLite, RAG citations, long-term memory, tool calling, human approvals, LLMOps observability, and optional Gemini provider support.
- Implemented a local-first agent workflow: intent detection, context retrieval from documents/memory/codebase, tool risk handling, approval gates, prompt assembly, cited answers, and fallback logging.
- Developed a Codebase Intelligence Skill that indexes repositories, extracts Python AST and TypeScript/JavaScript symbols, explains architecture, locates relevant files, and generates concrete test suggestions.
- Deployed a portfolio-ready AI Agent workspace with Vercel frontend and Render FastAPI backend, protected by per-session daily Gemini call limits and mock fallback.

## English Detailed Version

- Designed and implemented AgentOS Lite, a portfolio-ready AI Agent workspace that demonstrates the complete agent loop: user question, RAG/memory/codebase context retrieval, planning, tool selection, human approval, guarded answer generation, and LLMOps tracing.
- Built a FastAPI backend with SQLite persistence for conversations, documents, chunks, memories, tools, approvals, agent runs, model calls, retrieval logs, code files, symbols, scheduled tasks, and prompt templates.
- Built a Next.js + TypeScript dashboard with pages for Overview, Chat, Documents, Memory, Tools/Approvals, Codebase Intelligence, LLMOps, and Settings.
- Implemented deterministic mock LLM/embedding providers for zero-cost local demos, plus optional Gemini provider configuration with env-only secrets, manual health checks, fallback-to-mock behavior, and no-secret UI/LLMOps reporting.
- Added RAG quality features including TXT/Markdown upload, chunk preview, document title filtering, matched keyword snippets, citation cards, strict citation mode, and retrieval debug logs.
- Added guardrails that block dangerous tools, require human approval for risky tool calls, and never execute shell commands, delete files, or send emails in the MVP.

## 中文解释版

AgentOS Lite 是一个自托管 AI Agent 工作台 MVP。它的重点不是做一个普通聊天框，而是展示完整 AI Agent 产品架构：用户提问后，系统会根据意图从文档知识库、长期记忆、代码库索引中获取上下文，然后选择工具；高风险工具会暂停等待人工审批；最终回答带引用、带 trace，并且整个过程会被 LLMOps 记录。项目默认使用 Mock provider，零成本可运行，也支持可选 Gemini provider。

## 面试时怎么讲这个项目

可以这样讲：

我做 AgentOS Lite 是为了展示 AI 应用中聊天框背后的系统能力。普通 chatbot 很难解释答案来源，也很难控制工具执行风险。这个项目把一次回答建模为一个 Agent Run：先做 intent detection，再按需检索 RAG、Memory 或 Codebase，上下文进入 prompt assembly，然后根据工具风险决定直接执行、人工审批或阻止，最后生成带 citations 的回答，并在 LLMOps 中记录 provider、latency、tokens、retrieval、tool calls、fallback reason 和 trace。默认 mock 模式可以零成本跑完整流程，Gemini 只是可选真实模型。

## 技术关键词列表

- AI Agent
- RAG
- Long-term Memory
- Tool Calling
- Human-in-the-loop
- LLMOps
- Gemini Provider
- Codebase Intelligence
- AST Parsing
- FastAPI
- Next.js
- SQLite
- Guardrails
- Mock LLM
- Mock Embeddings
- Citation-backed QA
- Prompt Assembly
- Provider Fallback
