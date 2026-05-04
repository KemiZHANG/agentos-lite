# Resume Bullets

## English One-Line Version

Built AgentOS Lite, a deployed AI Agent workspace with RAG, memory, tool execution, human approval, LLMOps, Gemini integration, and codebase intelligence.

## English Three-Bullet Version

- Built a local-first AI Agent workspace using Next.js and FastAPI, integrating RAG document retrieval, long-term memory, tool execution, human-in-the-loop approvals, and LLMOps observability.
- Implemented Gemini provider integration with mock fallback, demo-mode rate limiting, and per-session daily call limits to protect public portfolio usage.
- Developed Codebase Intelligence with repository indexing, AST-based Python symbol extraction, TS/JS parsing, architecture explanation, and test suggestion generation.

## English Detailed Version

- Designed and shipped AgentOS Lite, a portfolio-ready AI Agent workspace that demonstrates the full agent loop: user question, context retrieval from documents/memory/codebase, planning, tool selection, human approval, cited answer generation, and LLMOps tracing.
- Built a FastAPI backend with SQLite persistence for conversations, messages, documents, chunks, memories, tools, approvals, agent runs, model calls, retrieval logs, code repositories, code files, symbols, scheduled tasks, and prompt templates.
- Built a Next.js + TypeScript dashboard with pages for Overview, Chat, Documents, Memory, Tools/Approvals, Codebase Intelligence, LLMOps, and Settings.
- Implemented deterministic mock LLM/embedding providers for zero-cost local demos, plus optional Gemini configuration with environment-only secrets, manual provider health checks, fallback-to-mock behavior, and no-secret UI/LLMOps reporting.
- Added hosted demo protection with anonymous session cookies, SQLite daily usage counters, a 5-call Gemini limit per UTC day, clear fallback notices, and LLMOps fallback reasons.
- Added RAG quality features including TXT/Markdown upload, chunk preview, document title filtering, matched-keyword snippets, citation cards, strict citation mode, and retrieval debug logs.
- Developed Codebase Intelligence that indexes repositories, extracts Python symbols with `ast`, parses TS/JS with lightweight regex, explains architecture by module, locates relevant files, and generates test suggestions.
- Deployed the project as a zero-cost portfolio demo with Vercel frontend and Render FastAPI backend, while documenting Render cold starts and SQLite ephemeral storage limitations honestly.

## 中文解释版

AgentOS Lite 是一个自托管 AI Agent 工作台 MVP，目标不是做一个普通聊天框，而是展示完整的 AI Agent 产品闭环。

用户提问后，系统会先做 intent detection，再按需从三个上下文来源取信息：文档知识库 RAG、长期记忆 Memory、代码库索引 Codebase。随后 Agent 会进行计划、选择工具、判断工具风险。如果工具是高风险操作，它会暂停并等待人工审批；如果是危险操作，例如 shell command、删除文件或发送邮件，MVP 会直接阻止。最终回答会带引用、trace、tool calls 和置信度信息，整个过程会进入 LLMOps，用于查看 provider、latency、tokens、retrieval logs、fallback reason 和错误。

技术亮点包括：

- Next.js + TypeScript + Tailwind 构建完整 Dashboard UI。
- FastAPI + SQLite 实现本地优先后端和持久化。
- Mock provider 默认零成本运行，不需要 API key。
- Gemini provider 可选开启，密钥只从环境变量读取。
- Hosted demo 使用匿名 session cookie 和每日 5 次 Gemini 调用限制，超限自动 mock fallback。
- RAG 支持 Markdown/TXT 上传、chunk preview、标题过滤、snippet citation 和 strict citation mode。
- Codebase Intelligence 支持 repo indexing、Python AST 符号提取、TS/JS 轻量解析、架构解释、相关文件定位和测试建议。
- Tools/Approvals 展示 human-in-the-loop 和 guardrails，而不是让模型随意执行动作。

## 面试时怎么讲

可以这样讲：

我做 AgentOS Lite 是为了展示 AI 应用里聊天框背后的系统能力。普通 chatbot 往往只有“输入 prompt -> 输出答案”，很难解释答案来源，也很难控制工具执行风险。AgentOS Lite 把一次回答建模为一个 Agent Run：先识别用户意图，再按需检索 RAG、Memory 或 Codebase，上下文进入 prompt assembly，然后根据工具风险决定直接执行、人工审批或阻止，最后生成带 citations 的回答，并在 LLMOps 中记录 provider、latency、tokens、retrieval、tool calls、fallback reason 和 trace。

这个项目默认用 mock 模式，所以任何人 clone 后都能零成本跑完整流程；如果配置 Gemini key，就可以切换到真实模型。线上作品集 demo 部署在 Vercel + Render，并且用匿名 session 每天 5 次 Gemini 调用限制保护 API key，超过后自动 fallback 到 mock。

## Technical Keywords

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
- Demo Rate Limiting
- Vercel
- Render
