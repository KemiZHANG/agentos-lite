from __future__ import annotations

from app.db.database import get_db, json_loads, rows_to_dicts


def dashboard() -> dict:
    with get_db() as conn:
        agent_runs = rows_to_dicts(conn.execute("SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT 50").fetchall())
        model_calls = rows_to_dicts(conn.execute("SELECT * FROM model_calls ORDER BY created_at DESC LIMIT 50").fetchall())
        retrieval_logs = rows_to_dicts(conn.execute("SELECT * FROM retrieval_logs ORDER BY created_at DESC LIMIT 50").fetchall())
        tool_calls = rows_to_dicts(conn.execute("SELECT * FROM tool_calls ORDER BY created_at DESC LIMIT 50").fetchall())
    for run in agent_runs:
        run["trace"] = json_loads(run.pop("trace_json", None), [])
    for log in retrieval_logs:
        log["results"] = json_loads(log.pop("results_json", None), [])
    for call in tool_calls:
        call["input"] = json_loads(call.pop("input_json", None), {})
        call["output"] = json_loads(call.pop("output_json", None), None)
    total_model_calls = len(model_calls)
    total_latency = sum(call.get("latency_ms", 0) for call in model_calls)
    errors = sum(1 for row in [*agent_runs, *model_calls, *tool_calls] if row.get("error"))
    fallback_count = sum(1 for call in model_calls if call.get("fallback_used"))
    return {
        "summary": {
            "agent_runs": len(agent_runs),
            "model_calls": total_model_calls,
            "avg_latency_ms": round(total_latency / total_model_calls, 1) if total_model_calls else 0,
            "tool_calls": len(tool_calls),
            "retrieval_logs": len(retrieval_logs),
            "errors": errors,
            "fallback_count": fallback_count,
            "provider": model_calls[0]["provider"] if model_calls else "mock",
        },
        "agent_runs": agent_runs,
        "model_calls": model_calls,
        "retrieval_logs": retrieval_logs,
        "tool_calls": tool_calls,
    }


def run_detail(agent_run_id: str) -> dict:
    with get_db() as conn:
        run = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (agent_run_id,)).fetchone()
        if run is None:
            raise KeyError(agent_run_id)
        model_calls = rows_to_dicts(conn.execute("SELECT * FROM model_calls WHERE agent_run_id = ? ORDER BY created_at", (agent_run_id,)).fetchall())
        retrieval_logs = rows_to_dicts(conn.execute("SELECT * FROM retrieval_logs WHERE agent_run_id = ? ORDER BY created_at", (agent_run_id,)).fetchall())
        tool_calls = rows_to_dicts(conn.execute("SELECT * FROM tool_calls WHERE agent_run_id = ? ORDER BY created_at", (agent_run_id,)).fetchall())
        messages = rows_to_dicts(
            conn.execute(
                """
                SELECT m.* FROM messages m
                JOIN agent_runs r ON r.conversation_id = m.conversation_id
                WHERE r.id = ?
                ORDER BY m.created_at
                """,
                (agent_run_id,),
            ).fetchall()
        )
    run_dict = dict(run)
    run_dict["trace"] = json_loads(run_dict.pop("trace_json", None), [])
    for log in retrieval_logs:
        log["results"] = json_loads(log.pop("results_json", None), [])
    for call in tool_calls:
        call["input"] = json_loads(call.pop("input_json", None), {})
        call["output"] = json_loads(call.pop("output_json", None), None)
    for message in messages:
        message["citations"] = json_loads(message.pop("citations_json", None), [])
        message["trace"] = json_loads(message.pop("trace_json", None), [])
        message["tool_calls"] = json_loads(message.pop("tool_calls_json", None), [])
    return {
        "agent_run": run_dict,
        "model_calls": model_calls,
        "retrieval_logs": retrieval_logs,
        "tool_calls": tool_calls,
        "messages": messages,
    }
