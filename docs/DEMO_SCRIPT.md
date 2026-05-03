# Demo Script

This is a 3-minute flow for interviews, GitHub walkthroughs, screenshots, or a short portfolio video.

## Before Recording

- Start backend with `.\scripts\start_backend.ps1`.
- Start frontend with `.\scripts\start_frontend.ps1`.
- Open `http://localhost:3000`.
- Use mock mode for a zero-cost recording, or Gemini mode only if your local key is configured.
- For the hosted demo, open the Vercel frontend URL and confirm Settings shows `Hosted demo`.

## 3-Minute Demo Flow

### 0:00-0:20 Overview

Open Overview.

Say: AgentOS Lite is a self-hosted AI Agent workspace. The core loop is user question -> context retrieval from RAG, memory, or codebase -> planning and tools -> human approval for risky actions -> cited answer -> LLMOps trace.

Show the flow cards: Ask, Retrieve context, Plan, Use tools, Require approval, Monitor runs.

### 0:20-0:40 Settings

Open Settings.

Show:

- active provider: mock or gemini
- active model
- key configured yes/no
- fallback enabled
- demo mode and call limits

Click `Test Provider`. Explain that Gemini is optional and that Settings never reveals the secret key.

For hosted demos, point out that each anonymous user gets 5 Gemini calls per UTC day, then mock fallback is used.

### 0:40-1:00 Chat Overview

Open Chat and ask:

```text
What can AgentOS Lite do?
```

Show the assistant answer, trace steps, and absence of fake citations for general chat.

### 1:00-1:25 Documents / RAG

Open Documents.

Load sample docs or upload `examples/sample_docs/product_brief.md`.

Show:

- document list
- chunk count
- chunk preview

Return to Chat and ask:

```text
Summarize the uploaded product brief.
```

Show inline citation labels and citation cards with document name, chunk label, snippet, and score.

### 1:25-1:45 Memory

Open Memory and add:

```text
I prefer concise technical explanations with practical examples.
```

Ask Chat:

```text
How should you explain technical topics to me?
```

Show that the answer uses the actual memory content.

### 1:45-2:20 Codebase Intelligence

Open Codebase.

Click `Index AgentOS Lite repo`.

Ask:

```text
Explain the architecture of this repo.
```

Show module-based architecture: frontend, backend API, services, RAG, LLM provider, memory, tools/approvals, codebase skill, LLMOps, docs/examples.

Then ask:

```text
Generate test suggestions for Gemini provider.
```

Show Suggested tests, Target files, Edge cases, Existing related tests, and Suggested test names or concrete test ideas.

### 2:20-2:40 Tools / Approvals

Open Tools.

Show:

- safe tools
- approval_required tools
- blocked dangerous tool
- pending/history approvals

Explain that the MVP never executes shell commands, deletes files, or sends emails.

### 2:40-3:00 LLMOps

Open LLMOps.

Show:

- provider and model
- latency
- fallback count/reason
- agent runs
- trace
- retrieval logs
- tool calls
- raw JSON available but collapsed

Close with: AgentOS Lite is a portfolio-ready local Agent workflow, not just a prompt UI.

## Hosted Demo Flow

Use this when the app is deployed with Vercel + Render.

1. Open the Vercel frontend.
2. Open Settings and show `Hosted demo`, provider/model, key configured yes/no, daily limit, remaining calls, and fallback enabled.
3. Click `Test Provider`.
4. Ask Chat: `What can AgentOS Lite do?`
5. Ask one document or codebase question.
6. Open LLMOps and show provider, latency, trace, fallback count, and fallback reason.
7. Explain: this public demo allows 5 real Gemini calls per anonymous session per day. After that, answers use mock fallback and are labeled as such.
