# Demo Script

This is a 3-minute video script for the deployed v0.1 portfolio demo.

Production URLs:

- Frontend: https://agentos-lite-jet.vercel.app
- Backend health: https://agentos-lite-backend.onrender.com/health

## Before Recording

- Open the Vercel frontend.
- Wait for Render to wake up if the first request is slow.
- Open Settings once and confirm `Hosted demo`, provider `gemini`, key configured `yes`, fallback enabled, daily limit `5`, and remaining calls.
- Do not spend all 5 Gemini calls while rehearsing. For a no-cost rehearsal, use local mock mode.

## 3-Minute Video Flow

### 0:00-0:20 Not Just A Chatbot

Open Overview.

Say:

AgentOS Lite is not just a prompt box. It is a local-first AI Agent workspace that turns each answer into an Agent Run: retrieve context from documents, memory, or codebase, plan the response, decide whether tools are safe, require approval for risky actions, answer with citations, and record everything in LLMOps.

Show:

- Hosted Demo Mode badge.
- Ask -> Retrieve context -> Plan -> Use tools -> Require approval -> Monitor runs.
- Try these demo actions.

### 0:20-0:40 Settings: Hosted Demo, Gemini, 5-Call Limit

Open Settings.

Show:

- current mode: `Hosted demo`
- provider: `gemini`
- active model
- API key configured: yes/no only
- fallback enabled
- daily limit: 5 calls per anonymous session per UTC day
- remaining calls

Say:

The Gemini key is stored only in Render environment variables. The UI never exposes the secret. Public demo usage is protected by a per-session daily limit; after 5 real Gemini calls, the app uses local mock fallback and records the fallback reason.

### 0:40-1:00 Chat Overview

Open Chat and ask:

```text
What can AgentOS Lite do?
```

Show:

- assistant answer
- trace steps
- no fake document citations for a general overview question
- provider/fallback state if visible in LLMOps later

### 1:00-1:25 Documents And RAG Citations

Open Documents.

Click `Use sample docs` or `Load sample workspace` from Overview.

Show:

- document list
- type
- chunk count
- chunk preview

Return to Chat and ask:

```text
Summarize the uploaded product brief.
```

Show:

- inline citation labels
- citation cards with document name, chunk label, snippet, matched evidence, and score

### 1:25-1:40 Memory

Open Memory.

Load or add this preference:

```text
I prefer concise technical explanations with practical examples.
```

Ask Chat:

```text
How should you explain technical topics to me?
```

Show that the answer uses the actual memory content naturally.

### 1:40-2:15 Codebase Intelligence

Open Codebase.

Click `Index sample repo` for a fast hosted demo, or `Index AgentOS Lite repo` if you want to show the project analyzing itself.

Ask:

```text
Explain the architecture of this repo.
```

Show:

- module-based architecture explanation
- file citations
- why files matched

Then ask:

```text
Generate test suggestions for Gemini provider.
```

Show:

- Suggested tests
- Target files
- Edge cases
- Existing related tests
- Suggested test names

### 2:15-2:35 Tools And Human Approval

Open Tools.

Show:

- safe tools
- approval_required tools
- blocked dangerous tool
- pending approvals and approval history
- readable tool-call logs

Say:

The MVP never executes shell commands from user input, never deletes files, and never sends emails. Risky operations pause for human review.

### 2:35-3:00 LLMOps

Open LLMOps.

Show:

- provider and model
- latency
- fallback count and fallback reason
- recent Agent Runs
- model calls
- retrieval logs
- tool calls
- raw JSON still available but collapsed

Close with:

AgentOS Lite is a portfolio-ready AI Agent system: RAG, memory, tools, approval, codebase intelligence, and LLMOps in one explainable workflow.

## Demo Limit Explanation

If the chat shows:

```text
You have reached today's Gemini demo limit. This response used the local mock fallback.
```

Say:

This is intentional. The public demo allows 5 real Gemini calls per anonymous session per UTC day, then switches to mock fallback so the project remains safe to share publicly.
