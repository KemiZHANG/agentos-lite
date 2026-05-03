from __future__ import annotations

import uuid
from typing import Any

from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now


def create_task(payload: dict[str, Any]) -> dict[str, Any]:
    task_id = str(uuid.uuid4())
    now = utc_now()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO scheduled_tasks (id, name, description, schedule, status, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                payload["name"],
                payload.get("description", ""),
                payload["schedule"],
                payload.get("status", "pending"),
                json_dumps(payload.get("payload", {})),
                now,
                now,
            ),
        )
    return get_task(task_id)


def list_tasks() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC").fetchall()
    tasks = rows_to_dicts(rows)
    for task in tasks:
        task["payload"] = json_loads(task.pop("payload_json", None), {})
    return tasks


def get_task(task_id: str) -> dict[str, Any]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise KeyError(task_id)
    task = dict(row)
    task["payload"] = json_loads(task.pop("payload_json", None), {})
    return task


def update_task(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_task(task_id)
    updated = {
        "name": payload.get("name", current["name"]),
        "description": payload.get("description", current["description"]),
        "schedule": payload.get("schedule", current["schedule"]),
        "status": payload.get("status", current["status"]),
        "payload": payload.get("payload", current["payload"]),
    }
    with get_db() as conn:
        conn.execute(
            """
            UPDATE scheduled_tasks
            SET name = ?, description = ?, schedule = ?, status = ?, payload_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated["name"],
                updated["description"],
                updated["schedule"],
                updated["status"],
                json_dumps(updated["payload"]),
                utc_now(),
                task_id,
            ),
        )
    return get_task(task_id)

