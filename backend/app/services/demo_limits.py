from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Request, Response

from app.core.config import get_settings
from app.db.database import get_db, utc_now


COOKIE_NAME = "agentos_demo_session"


@dataclass
class DemoLimitState:
    enabled: bool
    session_id: str
    date: str
    limit: int
    used: int
    remaining: int
    limited: bool


def resolve_demo_session(request: Request, response: Response | None = None) -> str:
    cookie_value = request.cookies.get(COOKIE_NAME)
    if cookie_value and _valid_cookie_value(cookie_value):
        return cookie_value
    settings = get_settings()
    production_cookie = settings.app_env == "production" or settings.demo_mode
    if response is None:
        return fallback_session_id(request)
    session_id = fallback_session_id(request) if production_cookie else str(uuid.uuid4())
    response.set_cookie(
        COOKIE_NAME,
        session_id,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=production_cookie,
        samesite="none" if production_cookie else "lax",
    )
    return session_id


def fallback_session_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    digest = hashlib.sha256(host.encode("utf-8")).hexdigest()[:32]
    return f"ip_{digest}"


def demo_limit_state(session_id: str) -> DemoLimitState:
    settings = get_settings()
    date = utc_day()
    limit = max(0, settings.max_llm_calls_per_user_per_day)
    enabled = settings.demo_mode and settings.llm_provider == "gemini"
    used = real_call_count(session_id, date) if enabled else 0
    remaining = max(0, limit - used) if enabled else limit
    return DemoLimitState(
        enabled=enabled,
        session_id=session_id,
        date=date,
        limit=limit,
        used=used,
        remaining=remaining,
        limited=enabled and used >= limit,
    )


def real_call_count(session_id: str, date: str | None = None, provider: str = "gemini") -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT real_llm_calls FROM demo_llm_usage WHERE session_id = ? AND date = ? AND provider = ?",
            (session_id, date or utc_day(), provider),
        ).fetchone()
    return int(row["real_llm_calls"] if row else 0)


def record_real_call(session_id: str, provider: str = "gemini") -> None:
    date = utc_day()
    now = utc_now()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO demo_llm_usage (id, session_id, date, provider, real_llm_calls, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(session_id, date, provider)
            DO UPDATE SET real_llm_calls = real_llm_calls + 1, updated_at = excluded.updated_at
            """,
            (str(uuid.uuid4()), session_id, date, provider, now, now),
        )


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _valid_cookie_value(value: str) -> bool:
    if value.startswith("ip_") and len(value) == 35:
        return all(char in "0123456789abcdef" for char in value[3:])
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
