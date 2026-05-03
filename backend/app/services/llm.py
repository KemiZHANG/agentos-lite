from __future__ import annotations

import re
import time
from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class ModelResult:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    provider: str = "mock"
    model: str = "mock-agentos-lite"


class MockLLMProvider:
    def generate(self, prompt: str, *, task_type: str = "general_chat", context: dict | None = None) -> ModelResult:
        started = time.perf_counter()
        context = context or {}
        chunks = context.get("retrieved_chunks", [])
        memories = context.get("memories", [])
        code_answer = context.get("code_answer", "")
        tool_seed = context.get("tool_seed", "")
        message = context.get("message", "")
        if task_type in {"general_chat", "project_overview"}:
            content = _memory_preference_answer(message, memories) if task_type == "general_chat" and _asks_about_user_preference(message) and memories else _project_overview(memories)
        elif task_type == "summarize_document":
            content = _summarize_chunks(chunks, memories)
        elif task_type == "document_qa":
            content = _answer_from_chunks(chunks, memories)
        elif task_type in {"codebase_question", "test_generation"}:
            content = code_answer or tool_seed or "No indexed codebase context matched this question. Index a repository first, then ask again."
        elif task_type == "memory_update":
            content = tool_seed or "I prepared a memory update request and paused it for human approval."
        elif task_type == "extract_tasks":
            content = "Here is a concise task breakdown with owners, dependencies, and likely next actions based on the available context."
        elif tool_seed:
            content = tool_seed
        else:
            content = "No relevant local context was found for this question, so I am answering in local mock mode."
        if memories and task_type not in {"general_chat", "project_overview"}:
            content += "\n\nMemory used: " + "; ".join(f"{item['title']}: {item['content']}" for item in memories[:3])
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ModelResult(
            content=content,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(content),
            latency_ms=latency_ms,
        )


def _project_overview(memories: list[dict]) -> str:
    memory_line = ""
    if memories:
        memory_line = "\n\nI also found a relevant preference/context memory: " + "; ".join(
            f"{item['title']}: {item['content']}" for item in memories[:3]
        )
    return (
        "AgentOS Lite is a self-hosted AI workspace MVP. It can run web chat, answer with RAG citations from uploaded TXT/Markdown docs, "
        "store long-term memory, call tools with risk levels, pause risky actions for human approval, keep scheduler-ready task records, "
        "show LLMOps logs for agent runs/model calls/retrieval/tool status, and provide codebase intelligence for repository questions and test suggestions."
        + memory_line
    )


def _asks_about_user_preference(message: str) -> bool:
    lower = message.lower()
    return any(term in lower for term in ["how should you", "explain", "to me", "my preference", "prefer"])


def _memory_preference_answer(message: str, memories: list[dict]) -> str:
    memory_text = "; ".join(f"{item['title']}: {item['content']}" for item in memories[:3])
    return (
        "Based on your saved memory, I should adapt to this preference: "
        f"{memory_text} "
        "So for technical topics, I will be concise, practical, and example-driven unless you ask for deeper detail."
    )


def _summarize_chunks(chunks: list[dict], memories: list[dict]) -> str:
    if not chunks:
        return "No relevant uploaded document context was found to summarize."
    source = chunks[0].get("document_name", "uploaded document")
    combined = " ".join(chunk.get("content", "") for chunk in chunks[:3])
    sentences = _sentences(combined)
    bullets = sentences[:4] or [combined[:240]]
    lines = [f"Summary of {source}:"]
    for index, sentence in enumerate(bullets, start=1):
        lines.append(f"- {sentence} [D{index if index <= len(chunks) else 1}]")
    if memories:
        lines.append("Relevant memory considered: " + "; ".join(f"{item['title']}: {item['content']}" for item in memories[:2]))
    return "\n".join(lines)


def _answer_from_chunks(chunks: list[dict], memories: list[dict]) -> str:
    if not chunks:
        return "No relevant local document context was found, so I cannot give a citation-backed document answer yet."
    lines = ["Based on the uploaded knowledge base:"]
    for index, chunk in enumerate(chunks[:3], start=1):
        snippet = chunk.get("short_snippet") or chunk.get("content", "")[:220]
        lines.append(f"- {snippet} [D{index}]")
    if memories:
        lines.append("I adapted this using memory: " + "; ".join(f"{item['title']}: {item['content']}" for item in memories[:2]))
    return "\n".join(lines)


def _sentences(text: str) -> list[str]:
    return [sentence.strip(" -\n\t") for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip(" -\n\t")]
