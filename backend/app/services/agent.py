from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.db.database import get_db, json_dumps, utc_now
from app.models.schemas import Citation, TraceStep
from app.services import codebase, demo_limits, memory, rag, tools
from app.services.llm import ModelResult, MockLLMProvider, build_system_instruction, estimate_tokens, get_llm_provider
from app.services.prompts import get_active_prompt


def detect_intent(message: str) -> str:
    lower = message.lower()
    if any(term in lower for term in ["remember", "save this", "my preference", "remember that"]):
        return "memory_update"
    if any(term in lower for term in ["test suggestion", "generate test", "tests for", "unit test"]):
        return "test_generation"
    if _has_explicit_codebase_intent(lower):
        return "codebase_question"
    if any(term in lower for term in ["what can agentos lite do", "what does agentos lite do", "agentos lite features", "what can this app do"]):
        return "project_overview"
    if any(term in lower for term in ["summarize", "summarise"]) and _likely_document_reference(lower):
        return "summarize_document"
    if "summary" in lower and _likely_document_reference(lower):
        return "summarize_document"
    if _looks_like_pasted_markdown(message):
        return "general_chat"
    if any(term in lower for term in ["report", "markdown report"]):
        return "generate_report"
    if any(term in lower for term in ["task", "todo", "action item"]):
        return "extract_tasks"
    if any(term in lower for term in ["document", "knowledge", "citation", "uploaded"]):
        return "document_qa"
    return "general_chat"


def run_chat(message: str, conversation_id: str | None = None, response_language: str = "en", demo_session_id: str | None = None) -> dict[str, Any]:
    user_id = get_settings().default_user_id
    conversation_id = conversation_id or str(uuid.uuid4())
    now = utc_now()
    intent = detect_intent(message)
    agent_run_id = str(uuid.uuid4())
    trace: list[TraceStep] = []
    tool_calls: list[dict[str, Any]] = []
    citations: list[Citation] = []
    approval_required = False
    confidence = "medium"

    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO conversations (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, user_id, _title_from_message(message), now, now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), conversation_id, "user", message, now),
        )
        conn.execute(
            """
            INSERT INTO agent_runs (id, conversation_id, user_id, intent, status, trace_json, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (agent_run_id, conversation_id, user_id, intent, "running", "[]", now),
        )

    def add_step(step: str, status: str, detail: str, data: dict[str, Any] | None = None) -> None:
        trace.append(TraceStep(step=step, status=status, detail=detail, data=data or {}))

    try:
        add_step("intent_detection", "completed", f"Detected intent: {intent}", {"intent": intent})
        add_step("planner", "completed", "Built a lightweight plan: memories, retrieval, tools, answer, verification.")

        memories = memory.retrieve_memories(message)
        add_step("memory_retrieval", "completed", f"Retrieved {len(memories)} relevant memories.", {"count": len(memories)})

        retrieved: list[dict[str, Any]] = []
        if _should_retrieve_documents(intent, message):
            retrieved = rag.retrieve(message, agent_run_id=agent_run_id)
            for index, item in enumerate(retrieved[:5], start=1):
                citations.append(_document_citation(item, index))
            add_step("rag_retrieval", "completed", f"Retrieved {len(retrieved)} document chunks.", {"count": len(retrieved)})
        else:
            add_step("rag_retrieval", "skipped", f"Skipped document retrieval for intent: {intent}.", {"intent": intent})

        if intent in {"codebase_question", "test_generation"}:
            if intent == "test_generation":
                code_result = codebase.generate_test_suggestions(message)
                tool_calls.append(tools.call_tool("generate_test_suggestions", {"target": message}, agent_run_id=agent_run_id))
                answer_seed = _format_test_suggestions(code_result)
                code_answer = answer_seed
            else:
                code_result = codebase.answer_repo_question(message)
                tool_calls.append(tools.call_tool("search_codebase", {"query": message}, agent_run_id=agent_run_id))
                answer_seed = code_result["answer"]
                code_answer = answer_seed
            for cite in code_result.get("citations", []):
                citations.append(_code_citation(cite))
            add_step("tool_selection", "completed", "Selected codebase intelligence tool.", {"tool": tool_calls[-1]["tool_name"]})
        elif intent == "memory_update":
            code_answer = ""
            call = tools.call_tool("save_memory", {"type": "note", "title": "User note", "content": message}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            approval_required = call["status"] == "approval_required"
            answer_seed = "I prepared a memory save request. It is paused for human approval before writing long-term memory."
            add_step("tool_selection", "paused" if approval_required else "completed", "Selected save_memory tool.", {"tool_status": call["status"]})
        elif intent == "generate_report":
            code_answer = ""
            context = "\n\n".join(item["content"] for item in retrieved[:3]) or message
            call = tools.call_tool("generate_markdown_report", {"title": "Generated Report", "body": context}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            approval_required = call["status"] == "approval_required"
            answer_seed = "I prepared a Markdown report generation request. Approval is required before the tool executes."
            add_step("tool_selection", "paused" if approval_required else "completed", "Selected generate_markdown_report tool.", {"tool_status": call["status"]})
        elif intent == "extract_tasks":
            code_answer = ""
            call = tools.call_tool("extract_task_list", {"text": message}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            answer_seed = _format_tasks(call.get("output", {}).get("tasks", []))
            add_step("tool_selection", "completed", "Selected extract_task_list tool.", {"tool_status": call["status"]})
        elif intent in {"document_qa", "summarize_document"}:
            code_answer = ""
            tool_calls.append(tools.call_tool("search_knowledge_base", {"query": message, "limit": 5}, agent_run_id=agent_run_id))
            answer_seed = ""
            add_step("tool_selection", "completed", "Selected knowledge base search tool.", {"tool": "search_knowledge_base"})
        else:
            code_answer = ""
            answer_seed = ""
            add_step("tool_selection", "skipped", "No tool needed for this local mock response.")

        prompt = _build_prompt(message, intent, memories, retrieved, answer_seed)
        prompt_template = get_active_prompt(intent)
        llm_context = {
            "message": message,
            "memories": memories,
            "retrieved_chunks": retrieved,
            "tool_seed": answer_seed,
            "code_answer": code_answer,
            "citations": [citation.model_dump() for citation in citations],
            "response_language": response_language,
        }
        demo_state = demo_limits.demo_limit_state(demo_session_id) if demo_session_id else None
        limit_fallback = _demo_limit_result(prompt, intent, llm_context, demo_state)
        if limit_fallback:
            model_result = limit_fallback
        else:
            llm = get_llm_provider()
            model_result = llm.generate(
                prompt_template["content"] + "\n" + prompt,
                task_type=intent,
                context=llm_context,
            )
            if demo_session_id and model_result.provider == "gemini" and model_result.status == "completed" and not model_result.fallback_used:
                demo_limits.record_real_call(demo_session_id)
                demo_state = demo_limits.demo_limit_state(demo_session_id)
        demo_session_day = demo_state.date if demo_state and demo_state.enabled else None
        _log_model_call(agent_run_id, model_result, prompt_template, demo_session_day=demo_session_day)
        _record_llm_usage(user_id, conversation_id, model_result)
        provider_label = "MockLLMProvider" if model_result.provider == "mock" else model_result.provider
        add_step("answer_generation", "completed", f"Generated response with {provider_label}.", {"provider": model_result.provider, "fallback_used": model_result.fallback_used})

        response = _compose_response(model_result.content, approval_required)
        fallback_notice = _fallback_notice(model_result)
        if fallback_notice:
            response += f"\n\n{fallback_notice}"
        if intent in {"document_qa", "summarize_document"} and not retrieved and get_settings().strict_citation_mode:
            confidence = "low"
            response += "\n\nConfidence: low because no document citation supported this answer."
        elif citations:
            confidence = "high"
        add_step("verification", "completed", f"Guardrails applied. Confidence: {confidence}.", {"confidence": confidence})
        add_step("final_response", "completed", "Final response prepared for UI.")

        message_id = str(uuid.uuid4())
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO messages
                (id, conversation_id, role, content, citations_json, trace_json, tool_calls_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    conversation_id,
                    "assistant",
                    response,
                    json_dumps([citation.model_dump() for citation in citations]),
                    json_dumps([step.model_dump() for step in trace]),
                    json_dumps(tool_calls),
                    utc_now(),
                ),
            )
            conn.execute(
                "UPDATE agent_runs SET status = ?, trace_json = ?, completed_at = ? WHERE id = ?",
                ("completed", json_dumps([step.model_dump() for step in trace]), utc_now(), agent_run_id),
            )
        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "provider": model_result.provider,
            "model": model_result.model,
            "attempted_provider": model_result.attempted_provider or model_result.provider,
            "fallback_used": model_result.fallback_used,
            "fallback_reason": model_result.fallback_reason,
            "fallback_notice": fallback_notice,
            "demo_remaining_calls": demo_state.remaining if demo_state and demo_state.enabled else None,
            "citations": [citation.model_dump() for citation in citations],
            "trace": [step.model_dump() for step in trace],
            "tool_calls": tool_calls,
            "approval_required": approval_required,
        }
    except Exception as exc:
        add_step("error", "failed", str(exc))
        with get_db() as conn:
            conn.execute(
                "UPDATE agent_runs SET status = ?, trace_json = ?, error = ?, completed_at = ? WHERE id = ?",
                ("failed", json_dumps([step.model_dump() for step in trace]), str(exc), utc_now(), agent_run_id),
            )
        raise


def list_conversations() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]


def list_messages(conversation_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,)).fetchall()
    return [dict(row) for row in rows]


def _title_from_message(message: str) -> str:
    return message.strip()[:48] or "New conversation"


def _build_prompt(message: str, intent: str, memories: list[dict[str, Any]], retrieved: list[dict[str, Any]], answer_seed: str) -> str:
    memory_text = "\n".join(f"- {item['title']} ({item['type']}): {item['content']}" for item in memories) or "None"
    context_text = "\n".join(
        f"[D{i + 1}] {item['document_name']} / {item.get('chunk_label', item['chunk_id'])}\n"
        f"Snippet: {item.get('short_snippet', '')}\n"
        f"Content: {item['content']}"
        for i, item in enumerate(retrieved[:5])
    ) or "None"
    tool_text = answer_seed or "None"
    return (
        f"System instruction:\n{build_system_instruction()}\n\n"
        f"Current intent: {intent}\n"
        f"User message:\n{message}\n\n"
        f"Relevant memories:\n{memory_text}\n\n"
        f"Retrieved document chunks:\n{context_text}\n\n"
        f"Tool/codebase context:\n{tool_text}\n\n"
        "Answer requirements:\n"
        "- Use citations like [D1] when document context is provided.\n"
        "- Use file paths when codebase context is provided.\n"
        "- If no context exists for a document-based question, say no relevant local context was found.\n"
    )


def _compose_response(base: str, approval_required: bool) -> str:
    parts = [base]
    if approval_required:
        parts.append("A tool call is paused until you approve or reject it in Tools and Approvals.")
    return "\n\n".join(parts)


def _likely_document_reference(lower: str) -> bool:
    return any(term in lower for term in ["document", "uploaded", "brief", ".md", ".txt", "knowledge base", "product brief"])


def _has_explicit_codebase_intent(lower: str) -> bool:
    codebase_terms = [
        "repo",
        "repository",
        "codebase",
        "authentication",
        "auth handled",
        "where is auth",
        "where is authentication",
        "files may be affected",
        "affected by this issue",
    ]
    if any(term in lower for term in codebase_terms):
        return True
    file_question = any(term in lower for term in ["which files", "what files", "relevant files", "locate files", "find files"])
    issue_question = "issue" in lower and any(term in lower for term in ["affected", "related", "impact", "files"])
    test_question = any(term in lower for term in ["test suggestions", "generate tests", "unit tests"])
    return file_question or issue_question or test_question


def _looks_like_pasted_markdown(message: str) -> bool:
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    markdown_markers = sum(1 for line in lines if line.startswith(("#", "-", "*", ">", "```", "|")))
    return markdown_markers >= 2


def _should_retrieve_documents(intent: str, message: str) -> bool:
    if intent in {"document_qa", "summarize_document", "generate_report"}:
        return True
    if intent == "extract_tasks" and _likely_document_reference(message.lower()):
        return True
    return False


def _document_citation(item: dict[str, Any], index: int) -> Citation:
    score = item.get("score")
    return Citation(
        source=f"D{index}",
        source_type="document",
        title=item.get("chunk_label") or f"{item['document_name']} chunk {index}",
        document_name=item["document_name"],
        chunk_id=item["chunk_id"],
        short_snippet=item.get("short_snippet") or item.get("content", "")[:220],
        relevance_score=score,
        score=score,
        metadata={"label": f"D{index}", "preview": item.get("short_snippet") or item.get("content", "")[:220]},
    )


def _code_citation(cite: dict[str, Any]) -> Citation:
    score = cite.get("score")
    file_path = cite.get("file_path") or cite.get("title")
    return Citation(
        source="codebase",
        source_type="codebase",
        title=file_path,
        file_path=file_path,
        short_snippet=cite.get("metadata", {}).get("match_reason") or f"Indexed code file: {file_path}",
        relevance_score=score,
        score=score,
        metadata={"label": "code", **cite.get("metadata", {})},
    )


def _format_tasks(tasks: list[str]) -> str:
    if not tasks:
        return "I did not find explicit task bullets, but I can still help turn this into a task list."
    return "Extracted tasks:\n" + "\n".join(f"- {task}" for task in tasks)


def _format_test_suggestions(result: dict[str, Any]) -> str:
    if not result.get("suggestions"):
        return "No indexed code matched the target yet. Index a repository first, then ask again."
    lines = ["Suggested tests"]
    for item in result["suggestions"][:5]:
        lines.append(f"- {item['file_path']}:")
        for suggestion in item["suggestions"]:
            lines.append(f"  - {suggestion}")
    lines.append("\nTarget files")
    target_files = result.get("target_files") or []
    for item in target_files[:6]:
        symbols = ", ".join(symbol["name"] for symbol in item.get("symbols", [])[:4])
        suffix = f" Symbols: {symbols}." if symbols else ""
        lines.append(f"- {item['path']}: {item.get('module_role', '')}{suffix}")
    lines.append("\nEdge cases")
    for edge_case in result.get("edge_cases", [])[:6]:
        lines.append(f"- {edge_case}")
    lines.append("\nExisting related tests")
    existing_tests = result.get("existing_related_tests") or []
    if not existing_tests:
        lines.append("- No existing related tests were found in the indexed repository.")
    for item in existing_tests:
        lines.append(f"- {item['path']}: {item.get('match_reason', '')}")
    return "\n".join(lines)


def _log_model_call(agent_run_id: str, model_result: Any, prompt_template: dict[str, Any], demo_session_day: str | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO model_calls
            (id, agent_run_id, attempted_provider, provider, model, prompt_template_name, prompt_template_version,
             input_tokens, output_tokens, latency_ms, status, created_at, fallback_used, fallback_reason, demo_session_day, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                agent_run_id,
                model_result.attempted_provider or model_result.provider,
                model_result.provider,
                model_result.model,
                prompt_template.get("name"),
                prompt_template.get("version"),
                model_result.input_tokens,
                model_result.output_tokens,
                model_result.latency_ms,
                model_result.status,
                utc_now(),
                1 if model_result.fallback_used else 0,
                model_result.fallback_reason,
                demo_session_day,
                model_result.error,
            ),
        )


def _demo_limit_result(prompt: str, intent: str, context: dict[str, Any], demo_state: demo_limits.DemoLimitState | None) -> Any | None:
    settings = get_settings()
    if not demo_state or not demo_state.enabled or not demo_state.limited:
        return None
    if not settings.demo_fallback_to_mock:
        return ModelResult(
            content="Daily Gemini demo limit reached. Mock fallback is disabled for this deployment.",
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens("Daily Gemini demo limit reached."),
            latency_ms=0,
            attempted_provider="gemini",
            provider="gemini",
            model=settings.gemini_model,
            status="failed",
            error="Daily Gemini demo limit reached.",
            fallback_reason="demo_daily_limit",
        )
    result = MockLLMProvider().generate(prompt, task_type=intent, context=context)
    result.attempted_provider = "gemini"
    result.fallback_used = True
    result.fallback_reason = "demo_daily_limit"
    result.error = "Daily Gemini demo limit reached."
    return result


def _fallback_notice(model_result: Any) -> str | None:
    if not model_result.fallback_used and model_result.fallback_reason != "demo_daily_limit":
        return None
    if model_result.fallback_reason == "demo_daily_limit":
        if not model_result.fallback_used:
            return "You have reached today's Gemini demo limit. Mock fallback is disabled for this deployment."
        return "You have reached today's Gemini demo limit. This answer used local mock fallback."
    if model_result.fallback_reason in {"missing_key", "provider_error"}:
        return "Gemini unavailable or demo limit reached, answered with local mock fallback."
    return None


def _record_llm_usage(user_id: str, session_id: str, model_result: Any) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO llm_usage_events (id, user_id, session_id, provider, fallback_used, fallback_reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), user_id, session_id, model_result.provider, 1 if model_result.fallback_used else 0, model_result.fallback_reason, utc_now()),
        )
