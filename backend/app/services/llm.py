from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.services import demo_limits


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class ModelResult:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    attempted_provider: str | None = None
    provider: str = "mock"
    model: str = "mock-agentos-lite"
    status: str = "completed"
    error: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


class ProviderConfigurationError(Exception):
    pass


class ProviderRuntimeError(Exception):
    pass


class MockLLMProvider:
    provider = "mock"
    model = "mock-agentos-lite"

    def generate(self, prompt: str, *, task_type: str = "general_chat", context: dict | None = None) -> ModelResult:
        started = time.perf_counter()
        context = context or {}
        chunks = context.get("retrieved_chunks", [])
        memories = context.get("memories", [])
        code_answer = context.get("code_answer", "")
        tool_seed = context.get("tool_seed", "")
        language = context.get("response_language", "en")
        message = context.get("message", "")
        if task_type in {"general_chat", "project_overview"}:
            content = (
                _memory_preference_answer(message, memories, language)
                if task_type == "general_chat" and _asks_about_user_preference(message) and memories
                else _project_overview(memories, language)
            )
        elif task_type == "summarize_document":
            content = _summarize_chunks(chunks, memories, language)
        elif task_type == "document_qa":
            content = _answer_from_chunks(chunks, memories, language)
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
            attempted_provider=self.provider,
        )


class GeminiProvider:
    provider = "gemini"

    def __init__(self, api_key: str | None, model: str, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client or httpx.Client(timeout=60)

    def generate(self, prompt: str, *, task_type: str = "general_chat", context: dict | None = None) -> ModelResult:
        if not self.api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is not configured.")
        started = time.perf_counter()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": build_system_instruction()}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        }
        response = self.client.post(url, params={"key": self.api_key}, json=payload)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise ProviderRuntimeError(_safe_error_message(response))
        data = response.json()
        content = _extract_gemini_text(data)
        usage = data.get("usageMetadata", {})
        return ModelResult(
            content=content,
            input_tokens=int(usage.get("promptTokenCount") or estimate_tokens(prompt)),
            output_tokens=int(usage.get("candidatesTokenCount") or estimate_tokens(content)),
            latency_ms=latency_ms,
            attempted_provider=self.provider,
            provider=self.provider,
            model=self.model,
        )


class FallbackLLMProvider:
    def __init__(self, primary: Any, fallback_to_mock: bool = True) -> None:
        self.primary = primary
        self.fallback_to_mock = fallback_to_mock
        self.mock = MockLLMProvider()

    def generate(self, prompt: str, *, task_type: str = "general_chat", context: dict | None = None) -> ModelResult:
        try:
            return self.primary.generate(prompt, task_type=task_type, context=context)
        except (ProviderConfigurationError, ProviderRuntimeError, httpx.HTTPError) as exc:
            message = str(exc)
            reason = "missing_key" if isinstance(exc, ProviderConfigurationError) else "provider_error"
            if self.fallback_to_mock:
                result = self.mock.generate(prompt, task_type=task_type, context=context)
                result.attempted_provider = getattr(self.primary, "provider", "unknown")
                result.fallback_used = True
                result.fallback_reason = reason
                result.error = message
                return result
            return ModelResult(
                content=f"Provider error: {message}",
                input_tokens=estimate_tokens(prompt),
                output_tokens=estimate_tokens(message),
                latency_ms=0,
                attempted_provider=getattr(self.primary, "provider", "unknown"),
                provider=getattr(self.primary, "provider", "unknown"),
                model=getattr(self.primary, "model", "unknown"),
                status="failed",
                error=message,
                fallback_reason=reason,
            )


def get_llm_provider() -> Any:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    if settings.llm_provider == "gemini":
        return FallbackLLMProvider(
            GeminiProvider(settings.gemini_api_key, settings.gemini_model),
            fallback_to_mock=settings.llm_fallback_to_mock,
        )
    return MockLLMProvider()


def provider_health_check(session_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    started = time.perf_counter()
    limit_state = demo_limits.demo_limit_state(session_id) if session_id else None
    base = {
        "provider": settings.llm_provider,
        "model": settings.active_model,
        "key_configured": settings.llm_api_key_configured,
        "fallback_available": settings.llm_fallback_to_mock,
        "fallback_used": False,
        "fallback_reason": None,
        "latency_ms": 0,
        "error": None,
        "demo_mode": settings.demo_mode,
        "max_calls_per_day": settings.max_llm_calls_per_user_per_day,
        "remaining_calls": limit_state.remaining if limit_state else None,
    }
    if settings.llm_provider == "mock":
        return {**base, "status": "success"}
    if limit_state and limit_state.limited:
        if settings.demo_fallback_to_mock:
            return {
                **base,
                "status": "fallback_used",
                "fallback_used": True,
                "fallback_reason": "demo_daily_limit",
                "error": "Daily Gemini demo limit reached. Provider health check used mock fallback.",
                "remaining_calls": 0,
            }
        return {**base, "status": "failed", "fallback_reason": "demo_daily_limit", "error": "Daily Gemini demo limit reached.", "remaining_calls": 0}
    result = get_llm_provider().generate(
        "Provider health check. Reply with: ok",
        task_type="general_chat",
        context={"message": "provider health check", "response_language": "en"},
    )
    if limit_state and limit_state.enabled and session_id and result.provider == "gemini" and result.status == "completed" and not result.fallback_used:
        demo_limits.record_real_call(session_id)
        limit_state = demo_limits.demo_limit_state(session_id)
    latency_ms = int((time.perf_counter() - started) * 1000)
    status = "success" if result.status == "completed" and not result.fallback_used else "fallback_used" if result.fallback_used else "failed"
    return {
        **base,
        "status": status,
        "latency_ms": latency_ms,
        "error": result.error,
        "fallback_used": result.fallback_used,
        "fallback_reason": result.fallback_reason,
        "remaining_calls": limit_state.remaining if limit_state else None,
    }


def build_system_instruction() -> str:
    return (
        "You are AgentOS Lite, a self-hosted AI Agent workspace assistant. Use the supplied intent, memories, "
        "retrieved document chunks, tool outputs, and codebase context. When document or code context is supplied, "
        "cite evidence using labels such as [D1] or file paths. If a document-based question has no relevant local "
        "context, say that no relevant local context was found. Never claim to execute shell commands, delete files, "
        "or send emails."
    )


def _extract_gemini_text(data: dict[str, Any]) -> str:
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()


def _safe_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
        message = data.get("error", {}).get("message") or data.get("message")
    except ValueError:
        message = response.text
    message = message or response.reason_phrase
    return f"HTTP {response.status_code}: {message[:500]}"


def _project_overview(memories: list[dict], language: str = "en") -> str:
    if language == "zh":
        memory_line = ""
        if memories:
            memory_line = "\n\n我还参考了相关记忆：" + "；".join(f"{item['title']}：{item['content']}" for item in memories[:3])
        return (
            "AgentOS Lite 是一个自托管 AI Agent 工作台 MVP。它支持 Web 聊天、基于上传 TXT/Markdown 文档的 RAG 引用、长期记忆、"
            "带风险等级的工具调用、人工审批、调度任务记录、LLMOps 日志，以及用于仓库问答和测试建议的代码库智能。"
            + memory_line
        )
    memory_line = ""
    if memories:
        memory_line = "\n\nI also found a relevant preference/context memory: " + "; ".join(
            f"{item['title']}: {item['content']}" for item in memories[:3]
        )
    return (
        "AgentOS Lite is a local-first AI Agent workspace MVP. It can run web chat, answer with RAG citations from uploaded TXT/Markdown docs, "
        "store long-term memory, call tools with risk levels, pause risky actions for human approval, keep scheduler-ready task records, "
        "show LLMOps logs for agent runs/model calls/retrieval/tool status, and provide codebase intelligence for repository questions and test suggestions."
        + memory_line
    )


def _asks_about_user_preference(message: str) -> bool:
    lower = message.lower()
    return any(term in lower for term in ["how should you", "explain", "to me", "my preference", "prefer"])


def _memory_preference_answer(message: str, memories: list[dict], language: str = "en") -> str:
    memory_text = "; ".join(f"{item['title']}: {item['content']}" for item in memories[:3])
    if language == "zh":
        zh_memory_text = "；".join(f"{item['title']}：{item['content']}" for item in memories[:3])
        return (
            "根据你保存的记忆，我应该这样适配你的偏好："
            f"{zh_memory_text}。"
            "所以讲技术主题时，我会保持简洁、实用，并尽量配合具体例子；如果你需要更深入，我再展开。"
        )
    return (
        "Based on your saved memory, I should adapt to this preference: "
        f"{memory_text} "
        "So for technical topics, I will be concise, practical, and example-driven unless you ask for deeper detail."
    )


def _summarize_chunks(chunks: list[dict], memories: list[dict], language: str = "en") -> str:
    if not chunks:
        return "没有找到可用于总结的相关上传文档上下文。" if language == "zh" else "No relevant uploaded document context was found to summarize."
    source = chunks[0].get("document_name", "uploaded document")
    combined = " ".join(chunk.get("content", "") for chunk in chunks[:3])
    sentences = _sentences(combined)
    bullets = sentences[:4] or [combined[:240]]
    if language == "zh":
        lines = [f"{source} 总结："]
        for index, sentence in enumerate(bullets, start=1):
            lines.append(f"- {sentence} [D{index if index <= len(chunks) else 1}]")
        if memories:
            lines.append("已参考相关记忆：" + "；".join(f"{item['title']}：{item['content']}" for item in memories[:2]))
        return "\n".join(lines)
    lines = [f"Summary of {source}:"]
    for index, sentence in enumerate(bullets, start=1):
        lines.append(f"- {sentence} [D{index if index <= len(chunks) else 1}]")
    if memories:
        lines.append("Relevant memory considered: " + "; ".join(f"{item['title']}: {item['content']}" for item in memories[:2]))
    return "\n".join(lines)


def _answer_from_chunks(chunks: list[dict], memories: list[dict], language: str = "en") -> str:
    if not chunks:
        return "没有找到相关本地文档上下文，因此无法给出带引用的文档回答。" if language == "zh" else "No relevant local document context was found, so I cannot give a citation-backed document answer yet."
    lines = ["基于上传知识库：" if language == "zh" else "Based on the uploaded knowledge base:"]
    for index, chunk in enumerate(chunks[:3], start=1):
        snippet = chunk.get("short_snippet") or chunk.get("content", "")[:220]
        lines.append(f"- {snippet} [D{index}]")
    if memories:
        prefix = "我还按记忆做了适配：" if language == "zh" else "I adapted this using memory: "
        lines.append(prefix + "; ".join(f"{item['title']}: {item['content']}" for item in memories[:2]))
    return "\n".join(lines)


def _sentences(text: str) -> list[str]:
    return [sentence.strip(" -\n\t") for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip(" -\n\t")]
