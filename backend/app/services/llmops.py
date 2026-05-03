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
    return {
        "summary": {
            "agent_runs": len(agent_runs),
            "model_calls": total_model_calls,
            "avg_latency_ms": round(total_latency / total_model_calls, 1) if total_model_calls else 0,
            "tool_calls": len(tool_calls),
            "retrieval_logs": len(retrieval_logs),
        },
        "agent_runs": agent_runs,
        "model_calls": model_calls,
        "retrieval_logs": retrieval_logs,
        "tool_calls": tool_calls,
    }

