# Demo Script

Use this flow for interviews, README screenshots, or a GitHub walkthrough.

1. Start the backend and frontend.
2. Open Overview and describe the loop: ask, retrieve context, plan, use tools, require approval, monitor runs.
3. Open Settings. Show that mock mode costs `$0`. If Gemini is configured, show provider/model/key configured yes/no and click `Test Provider`.
4. Open Chat and ask: `What can AgentOS Lite do?`
5. Open Documents and load or upload `examples/sample_docs/product_brief.md`.
6. View chunk preview cards, then ask Chat: `Summarize the uploaded product brief.`
7. Open Memory, add a preference such as `I prefer concise technical explanations with practical examples.`
8. Ask Chat: `How should you explain technical topics to me?`
9. Open Codebase and click `Index sample repo` or `Index AgentOS Lite repo`.
10. Ask: `Explain the architecture of this repo.`
11. Ask: `Which files are related to document upload?`
12. Ask: `Generate test suggestions for document upload.`
13. Open Tools and trigger a risky memory/report action from Chat. Approve or reject it.
14. Open LLMOps and inspect recent runs, provider/model status, retrieval snippets, tool calls, fallback reason, and raw JSON.

Suggested close: AgentOS Lite is local-first and intentionally mock-first, with Gemini optional and guarded by env configuration plus fallback logging.
