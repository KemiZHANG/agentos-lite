from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable

from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now
from app.services import codebase, memory, rag


ToolExecutor = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    risk_level: str
    execute: ToolExecutor


def _search_knowledge_base(payload: dict[str, Any]) -> dict[str, Any]:
    return {"results": rag.retrieve(payload.get("query", ""), limit=payload.get("limit", 5))}


def _generate_markdown_report(payload: dict[str, Any]) -> dict[str, Any]:
    title = payload.get("title", "AgentOS Lite Report")
    body = payload.get("body", "")
    return {"markdown": f"# {title}\n\n{body}\n\n_Generated locally by AgentOS Lite._"}


def _extract_task_list(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text", "")
    tasks = [line.strip("- []\t ") for line in text.splitlines() if line.strip().startswith(("-", "*", "[ ]"))]
    if not tasks and text:
        tasks = [sentence.strip() for sentence in text.split(".") if "todo" in sentence.lower() or "task" in sentence.lower()]
    return {"tasks": tasks[:20]}


def _save_memory(payload: dict[str, Any]) -> dict[str, Any]:
    created = memory.create_memory(
        {
            "type": payload.get("type", "note"),
            "title": payload.get("title", "Saved by agent"),
            "content": payload.get("content", ""),
            "metadata": {"source": "tool"},
        }
    )
    return {"memory": created}


def _search_codebase(payload: dict[str, Any]) -> dict[str, Any]:
    return {"results": codebase.search_codebase(payload.get("query", ""), payload.get("repository_id"))}


def _generate_test_suggestions(payload: dict[str, Any]) -> dict[str, Any]:
    return codebase.generate_test_suggestions(payload.get("target", ""), payload.get("repository_id"))


TOOLS: dict[str, Tool] = {
    "search_knowledge_base": Tool(
        "search_knowledge_base",
        "Search uploaded document chunks and return citations.",
        {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}},
        "safe",
        _search_knowledge_base,
    ),
    "generate_markdown_report": Tool(
        "generate_markdown_report",
        "Generate a Markdown report from supplied text.",
        {"type": "object", "properties": {"title": {"type": "string"}, "body": {"type": "string"}}},
        "approval_required",
        _generate_markdown_report,
    ),
    "extract_task_list": Tool(
        "extract_task_list",
        "Extract task-like bullet items from text.",
        {"type": "object", "properties": {"text": {"type": "string"}}},
        "safe",
        _extract_task_list,
    ),
    "save_memory": Tool(
        "save_memory",
        "Save long-term memory for the default local user.",
        {"type": "object", "properties": {"type": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"}}},
        "approval_required",
        _save_memory,
    ),
    "search_codebase": Tool(
        "search_codebase",
        "Search indexed codebase files.",
        {"type": "object", "properties": {"query": {"type": "string"}}},
        "safe",
        _search_codebase,
    ),
    "generate_test_suggestions": Tool(
        "generate_test_suggestions",
        "Generate test suggestions for code.",
        {"type": "object", "properties": {"target": {"type": "string"}}},
        "safe",
        _generate_test_suggestions,
    ),
}


def register_tools() -> None:
    with get_db() as conn:
        for tool in TOOLS.values():
            conn.execute(
                """
                INSERT OR REPLACE INTO tools (name, description, input_schema_json, risk_level, enabled)
                VALUES (?, ?, ?, ?, 1)
                """,
                (tool.name, tool.description, json_dumps(tool.input_schema), tool.risk_level),
            )


def list_tools() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tools ORDER BY name").fetchall()
    tools = rows_to_dicts(rows)
    for tool in tools:
        tool["input_schema"] = json_loads(tool.pop("input_schema_json", None), {})
        tool["enabled"] = bool(tool["enabled"])
    return tools


def call_tool(name: str, payload: dict[str, Any], agent_run_id: str | None = None) -> dict[str, Any]:
    tool = TOOLS[name]
    call_id = str(uuid.uuid4())
    now = utc_now()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO tool_calls
            (id, agent_run_id, tool_name, input_json, status, risk_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (call_id, agent_run_id, name, json_dumps(payload), "created", tool.risk_level, now),
        )
    if tool.risk_level == "blocked":
        with get_db() as conn:
            conn.execute(
                "UPDATE tool_calls SET status = ?, error = ?, completed_at = ? WHERE id = ?",
                ("blocked", "Blocked by MVP guardrails", utc_now(), call_id),
            )
        return {"id": call_id, "tool_name": name, "status": "blocked", "risk_level": tool.risk_level, "error": "Blocked by MVP guardrails"}
    if tool.risk_level == "approval_required":
        approval_id = str(uuid.uuid4())
        with get_db() as conn:
            conn.execute(
                "UPDATE tool_calls SET status = ? WHERE id = ?",
                ("approval_required", call_id),
            )
            conn.execute(
                """
                INSERT INTO approval_requests
                (id, tool_call_id, status, reason, requested_payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (approval_id, call_id, "pending", f"Tool {name} requires human approval.", json_dumps(payload), utc_now()),
            )
        return {"id": call_id, "approval_id": approval_id, "tool_name": name, "status": "approval_required", "risk_level": tool.risk_level}
    try:
        output = tool.execute(payload)
        with get_db() as conn:
            conn.execute(
                "UPDATE tool_calls SET status = ?, output_json = ?, completed_at = ? WHERE id = ?",
                ("completed", json_dumps(output), utc_now(), call_id),
            )
        return {"id": call_id, "tool_name": name, "status": "completed", "risk_level": tool.risk_level, "output": output}
    except Exception as exc:
        with get_db() as conn:
            conn.execute(
                "UPDATE tool_calls SET status = ?, error = ?, completed_at = ? WHERE id = ?",
                ("failed", str(exc), utc_now(), call_id),
            )
        return {"id": call_id, "tool_name": name, "status": "failed", "risk_level": tool.risk_level, "error": str(exc)}


def list_tool_calls() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tool_calls ORDER BY created_at DESC LIMIT 100").fetchall()
    calls = rows_to_dicts(rows)
    for call in calls:
        call["input"] = json_loads(call.pop("input_json", None), {})
        call["output"] = json_loads(call.pop("output_json", None), None)
    return calls


def list_approvals() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT a.*, t.tool_name, t.risk_level
            FROM approval_requests a
            JOIN tool_calls t ON t.id = a.tool_call_id
            ORDER BY a.created_at DESC
            """
        ).fetchall()
    approvals = rows_to_dicts(rows)
    for approval in approvals:
        approval["requested_payload"] = json_loads(approval.pop("requested_payload_json", None), {})
    return approvals


def decide_approval(approval_id: str, status: str, reviewer_note: str | None = None) -> dict[str, Any]:
    if status not in {"approved", "rejected"}:
        raise ValueError("status must be approved or rejected")
    approvals = {approval["id"]: approval for approval in list_approvals()}
    if approval_id not in approvals:
        raise KeyError(approval_id)
    approval = approvals[approval_id]
    with get_db() as conn:
        conn.execute(
            "UPDATE approval_requests SET status = ?, reviewer_note = ?, resolved_at = ? WHERE id = ?",
            (status, reviewer_note, utc_now(), approval_id),
        )
    if status == "rejected":
        with get_db() as conn:
            conn.execute(
                "UPDATE tool_calls SET status = ?, error = ?, completed_at = ? WHERE id = ?",
                ("rejected", "Rejected by human reviewer", utc_now(), approval["tool_call_id"]),
            )
        return {**approval, "status": "rejected", "reviewer_note": reviewer_note}
    tool = TOOLS[approval["tool_name"]]
    output = tool.execute(approval["requested_payload"])
    with get_db() as conn:
        conn.execute(
            "UPDATE tool_calls SET status = ?, output_json = ?, completed_at = ? WHERE id = ?",
            ("completed", json_dumps(output), utc_now(), approval["tool_call_id"]),
        )
    return {**approval, "status": "approved", "reviewer_note": reviewer_note, "output": output}
