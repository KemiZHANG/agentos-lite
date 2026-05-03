# Product Story

AgentOS Lite is not positioned as a generic chatbot. It is a self-hosted AI Agent workspace for local project work.

## User

The initial user is a developer, builder, or technical operator who wants an AI assistant that can reason over local documents, remembered preferences, and code repositories without depending on a hosted SaaS workflow.

## Pain

- Chat answers are hard to verify when they have no citations.
- Project context is scattered across notes, docs, code, and memory.
- Tool-using agents can be unsafe without approval gates.
- Model calls and retrieval decisions are difficult to debug.
- Portfolio AI projects often show UI polish but not agent architecture.

## Solution

AgentOS Lite turns each question into an auditable agent run:

1. Detect intent.
2. Retrieve relevant memory, document chunks, or code files only when needed.
3. Select tools based on the task.
4. Pause risky tools for human approval.
5. Generate an answer using mock or optional Gemini.
6. Verify citations and confidence.
7. Log the run in LLMOps.

## Why It Is Different From a Chatbot

The product surface is a workspace: documents, memory, codebase, tools, approvals, provider settings, and LLMOps all connect to the same agent loop. The answer is only the visible end of a traceable system.
