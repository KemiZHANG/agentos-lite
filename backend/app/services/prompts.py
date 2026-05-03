from __future__ import annotations

import uuid

from app.db.database import get_db, utc_now


DEFAULT_PROMPTS = [
    ("agent_answer", "1.0.0", "general_chat", "Answer as AgentOS Lite using memories, retrieved context, tool outputs, citations, and guardrails."),
    ("project_overview", "1.0.0", "project_overview", "Explain AgentOS Lite capabilities without inventing retrieved context."),
    ("document_qa", "1.0.0", "document_qa", "Use retrieved document chunks. If no citation supports the answer, mark confidence low."),
    ("codebase_qa", "1.0.0", "codebase_question", "Use indexed code files and symbols. Cite file paths."),
]


def seed_prompts() -> None:
    with get_db() as conn:
        for name, version, task_type, content in DEFAULT_PROMPTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO prompt_templates
                (id, name, version, task_type, content, active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (str(uuid.uuid4()), name, version, task_type, content, utc_now()),
            )


def get_active_prompt(task_type: str) -> dict[str, str]:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM prompt_templates
            WHERE task_type = ? AND active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (task_type,),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT * FROM prompt_templates WHERE name = 'agent_answer' AND active = 1 LIMIT 1"
            ).fetchone()
    if row is None:
        return {"name": "inline", "version": "0", "content": "Answer helpfully."}
    return dict(row)


def list_prompts() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM prompt_templates ORDER BY name, version").fetchall()
    return [dict(row) for row in rows]
