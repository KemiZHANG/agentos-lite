# GitHub Profile Setup

Use this checklist after the v0.1 release is pushed.

## Repository Description

Suggested description:

```text
Local-first AI Agent workspace with RAG, memory, tools, approvals, LLMOps, Gemini, and codebase intelligence.
```

Shorter option:

```text
Self-hosted AI Agent workspace with RAG, memory, LLMOps, Gemini, and codebase intelligence.
```

## Topics

Add these repository topics:

- `ai-agent`
- `rag`
- `llmops`
- `fastapi`
- `nextjs`
- `gemini`
- `codebase-intelligence`
- `human-in-the-loop`
- `tool-calling`
- `sqlite`
- `portfolio-project`
- `mock-llm`

## Pin To GitHub Profile

1. Open your GitHub profile.
2. Click `Customize your pins`.
3. Search for `agentos-lite`.
4. Select the repository.
5. Save the pinned repositories.

## README First Screen

The first screen should show:

- One-sentence product description.
- Live Demo link.
- Backend Health link.
- Local run guide link.
- Tech tags.
- Why this is not just a chatbot.
- Key features.

This lets a reviewer understand the project before scrolling.

## Demo Video Link

Recommended after recording:

1. Upload a 2-3 minute walkthrough to YouTube, Loom, Bilibili, or a GitHub release asset.
2. Add a `Demo Video` link near the top of `README.md`.
3. Use `docs/DEMO_SCRIPT.md` as the narration outline.
4. Capture screenshots listed in `docs/SCREENSHOTS_TO_CAPTURE.md`.

Suggested video title:

```text
AgentOS Lite v0.1: RAG, Memory, Tools, Approvals, LLMOps, and Codebase Intelligence
```

## Manual Checks Before Sharing

- Open the Live Demo URL in a private browser window.
- Confirm Settings shows `Hosted demo`, Gemini provider, key configured yes/no only, and daily limit.
- Confirm no page shows a real API key.
- Confirm Render backend wakes up and `/health` returns `ok`.
- Confirm README links work.
- Confirm screenshots do not expose local paths, `.env`, or secrets.
