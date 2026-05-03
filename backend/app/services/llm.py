from __future__ import annotations

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
    def generate(self, prompt: str, *, task_type: str = "general_chat") -> ModelResult:
        started = time.perf_counter()
        lower = prompt.lower()
        if "codebase" in task_type or "repository" in lower:
            content = (
                "Based on the indexed repository, the relevant files and symbols are listed in the citations. "
                "The architecture appears to be organized around small modules, explicit service boundaries, "
                "and testable functions. Review the cited files first because they contain the strongest matches."
            )
        elif "context:" in lower and "citation" in lower:
            content = (
                "I found relevant knowledge base context and used it to answer. "
                "The cited chunks are the best local evidence for this response, so confidence is higher when they match your question closely."
            )
        elif "task" in lower:
            content = "Here is a concise task breakdown with owners, dependencies, and likely next actions based on the available context."
        else:
            content = (
                "I am running in MockLLM mode, so this response is deterministic and local. "
                "I can still use memory, retrieved documents, codebase citations, tools, and approval flow to produce a useful MVP answer."
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ModelResult(
            content=content,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(content),
            latency_ms=latency_ms,
        )

