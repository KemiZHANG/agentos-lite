from __future__ import annotations

import uuid
from typing import Any

from app.core.config import get_settings
from app.db.database import get_db, json_dumps, json_loads, rows_to_dicts, utc_now


def create_memory(payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    now = utc_now()
    memory_id = str(uuid.uuid4())
    user_id = user_id or get_settings().default_user_id
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO memories (id, user_id, type, title, content, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                user_id,
                payload.get("type", "note"),
                payload["title"],
                payload["content"],
                json_dumps(payload.get("metadata", {})),
                now,
                now,
            ),
        )
    return get_memory(memory_id)


def list_memories(query: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
    user_id = user_id or get_settings().default_user_id
    with get_db() as conn:
        if query:
            like = f"%{query.lower()}%"
            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE user_id = ? AND (lower(title) LIKE ? OR lower(content) LIKE ? OR lower(type) LIKE ?)
                ORDER BY updated_at DESC
                """,
                (user_id, like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
    return [_decode_memory(row) for row in rows_to_dicts(rows)]


def get_memory(memory_id: str) -> dict[str, Any]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row is None:
        raise KeyError(memory_id)
    return _decode_memory(dict(row))


def update_memory(memory_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_memory(memory_id)
    updated = {
        "type": payload.get("type", current["type"]),
        "title": payload.get("title", current["title"]),
        "content": payload.get("content", current["content"]),
        "metadata": payload.get("metadata", current["metadata"]),
    }
    with get_db() as conn:
        conn.execute(
            """
            UPDATE memories
            SET type = ?, title = ?, content = ?, metadata_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated["type"],
                updated["title"],
                updated["content"],
                json_dumps(updated["metadata"]),
                utc_now(),
                memory_id,
            ),
        )
    return get_memory(memory_id)


def delete_memory(memory_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))


def retrieve_memories(query: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = {term for term in query.lower().split() if len(term) > 2}
    scored: list[tuple[int, dict[str, Any]]] = []
    for memory in list_memories():
        haystack = f"{memory['type']} {memory['title']} {memory['content']}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, memory))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [memory for _, memory in scored[:limit]]


def _decode_memory(row: dict[str, Any]) -> dict[str, Any]:
    row["metadata"] = json_loads(row.pop("metadata_json", None), {})
    return row

