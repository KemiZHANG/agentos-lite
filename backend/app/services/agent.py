from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.db.database import get_db, json_dumps, utc_now
from app.models.schemas import Citation, TraceStep
from app.services import codebase, memory, rag, tools
from app.services.llm import MockLLMProvider
from app.services.prompts import get_active_prompt


llm = MockLLMProvider()


def detect_intent(message: str) -> str:
    lower = message.lower()
    if any(term in lower for term in ["remember", "save this", "my preference"]):
        return "memory_update"
    if any(term in lower for term in ["test suggestion", "generate test", "tests for", "unit test"]):
        return "test_generation"
    if any(term in lower for term in ["repo", "codebase", "function", "authentication", "auth handled", "file", "architecture"]):
        return "codebase_question"
    if any(term in lower for term in ["summarize", "summary"]):
        return "summarize_document"
    if any(term in lower for term in ["report", "markdown report"]):
        return "generate_report"
    if any(term in lower for term in ["task", "todo", "action item"]):
        return "extract_tasks"
    if any(term in lower for term in ["document", "knowledge", "citation", "uploaded"]):
        return "document_qa"
    return "general_chat"


def run_chat(message: str, conversation_id: str | None = None) -> dict[str, Any]:
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

        retrieved = rag.retrieve(message, agent_run_id=agent_run_id)
        for item in retrieved[:5]:
            citations.append(
                Citation(
                    source="document",
                    title=item["document_name"],
                    chunk_id=item["chunk_id"],
                    score=item["score"],
                    metadata={"preview": item["content"][:180]},
                )
            )
        add_step("rag_retrieval", "completed", f"Retrieved {len(retrieved)} document chunks.", {"count": len(retrieved)})

        if intent in {"codebase_question", "test_generation"}:
            if intent == "test_generation":
                code_result = codebase.generate_test_suggestions(message)
                tool_calls.append(tools.call_tool("generate_test_suggestions", {"target": message}, agent_run_id=agent_run_id))
                answer_seed = _format_test_suggestions(code_result)
            else:
                code_result = codebase.answer_repo_question(message)
                tool_calls.append(tools.call_tool("search_codebase", {"query": message}, agent_run_id=agent_run_id))
                answer_seed = code_result["answer"]
            for cite in code_result.get("citations", []):
                citations.append(Citation(**cite))
            add_step("tool_selection", "completed", "Selected codebase intelligence tool.", {"tool": tool_calls[-1]["tool_name"]})
        elif intent == "memory_update":
            call = tools.call_tool("save_memory", {"type": "note", "title": "User note", "content": message}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            approval_required = call["status"] == "approval_required"
            answer_seed = "I prepared a memory save request. It is paused for human approval before writing long-term memory."
            add_step("tool_selection", "paused" if approval_required else "completed", "Selected save_memory tool.", {"tool_status": call["status"]})
        elif intent == "generate_report":
            context = "\n\n".join(item["content"] for item in retrieved[:3]) or message
            call = tools.call_tool("generate_markdown_report", {"title": "Generated Report", "body": context}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            approval_required = call["status"] == "approval_required"
            answer_seed = "I prepared a Markdown report generation request. Approval is required before the tool executes."
            add_step("tool_selection", "paused" if approval_required else "completed", "Selected generate_markdown_report tool.", {"tool_status": call["status"]})
        elif intent == "extract_tasks":
            call = tools.call_tool("extract_task_list", {"text": message}, agent_run_id=agent_run_id)
            tool_calls.append(call)
            answer_seed = _format_tasks(call.get("output", {}).get("tasks", []))
            add_step("tool_selection", "completed", "Selected extract_task_list tool.", {"tool_status": call["status"]})
        else:
            tool_calls.append(tools.call_tool("search_knowledge_base", {"query": message, "limit": 5}, agent_run_id=agent_run_id))
            answer_seed = ""
            add_step("tool_selection", "completed", "Selected knowledge base search tool.", {"tool": "search_knowledge_base"})

        prompt = _build_prompt(message, intent, memories, retrieved, answer_seed)
        prompt_template = get_active_prompt(intent)
        model_result = llm.generate(prompt_template["content"] + "\n" + prompt, task_type=intent)
        _log_model_call(agent_run_id, model_result, prompt_template)
        add_step("answer_generation", "completed", "Generated response with MockLLMProvider.", {"provider": model_result.provider})

        response = _compose_response(model_result.content, answer_seed, memories, retrieved, approval_required)
        if intent in {"document_qa", "summarize_document"} and not citations:
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
    memory_text = "\n".join(f"- {item['title']}: {item['content']}" for item in memories)
    context_text = "\n".join(f"Citation {i + 1}: {item['document_name']}#{item['chunk_id']}\n{item['content']}" for i, item in enumerate(retrieved[:5]))
    return f"Intent: {intent}\nUser: {message}\nMemories:\n{memory_text}\nContext:\n{context_text}\nTool seed:\n{answer_seed}"


def _compose_response(base: str, seed: str, memories: list[dict[str, Any]], retrieved: list[dict[str, Any]], approval_required: bool) -> str:
    parts = []
    if seed:
        parts.append(seed)
    parts.append(base)
    if memories:
        parts.append("Relevant memory considered: " + "; ".join(memory["title"] for memory in memories[:3]) + ".")
    if retrieved:
        parts.append("Citations are attached from the local knowledge base.")
    if approval_required:
        parts.append("A tool call is paused until you approve or reject it in Tools and Approvals.")
    return "\n\n".join(parts)


def _format_tasks(tasks: list[str]) -> str:
    if not tasks:
        return "I did not find explicit task bullets, but I can still help turn this into a task list."
    return "Extracted tasks:\n" + "\n".join(f"- {task}" for task in tasks)


def _format_test_suggestions(result: dict[str, Any]) -> str:
    if not result.get("suggestions"):
        return "No indexed code matched the target yet. Index a repository first, then ask again."
    lines = ["Test suggestions from codebase intelligence:"]
    for item in result["suggestions"]:
        lines.append(f"- {item['file_path']}: " + " ".join(item["suggestions"]))
    return "\n".join(lines)


def _log_model_call(agent_run_id: str, model_result: Any, prompt_template: dict[str, Any]) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO model_calls
            (id, agent_run_id, provider, model, prompt_template_name, prompt_template_version,
             input_tokens, output_tokens, latency_ms, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                agent_run_id,
                model_result.provider,
                model_result.model,
                prompt_template.get("name"),
                prompt_template.get("version"),
                model_result.input_tokens,
                model_result.output_tokens,
                model_result.latency_ms,
                "completed",
                utc_now(),
            ),
        )

