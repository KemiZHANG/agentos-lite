from starlette.requests import Request
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import get_db, init_db
from app.main import app
from app.services import demo_limits, llm
from app.services.llm import ModelResult
from app.services.prompts import seed_prompts
from app.services.tools import register_tools


class FakeGeminiProvider:
    provider = "gemini"

    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt, *, task_type="general_chat", context=None):
        return ModelResult(
            content="Gemini mocked response",
            input_tokens=4,
            output_tokens=3,
            latency_ms=7,
            attempted_provider="gemini",
            provider="gemini",
            model=self.model,
        )


class FailingGeminiProvider(FakeGeminiProvider):
    def generate(self, prompt, *, task_type="general_chat", context=None):
        from app.services.llm import ProviderRuntimeError

        raise ProviderRuntimeError("mock provider failure")


def test_demo_session_cookie_created(tmp_path, monkeypatch):
    _setup_demo(tmp_path, monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        response = client.get("/settings")
    assert response.status_code == 200
    assert demo_limits.COOKIE_NAME in response.cookies
    assert response.json()["current_mode"] == "hosted_demo"


def test_demo_limit_first_five_calls_use_gemini_and_sixth_falls_back(tmp_path, monkeypatch):
    _setup_demo(tmp_path, monkeypatch)
    monkeypatch.setattr(llm, "GeminiProvider", FakeGeminiProvider)
    with TestClient(app, base_url="https://testserver") as client:
        providers = []
        for _ in range(5):
            body = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()
            providers.append(body["provider"])
            assert body["fallback_used"] is False
        sixth = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()

    assert providers == ["gemini"] * 5
    assert sixth["provider"] == "mock"
    assert sixth["attempted_provider"] == "gemini"
    assert sixth["fallback_used"] is True
    assert sixth["fallback_reason"] == "demo_daily_limit"
    assert "today's Gemini demo limit" in sixth["fallback_notice"]
    with get_db() as conn:
        usage = conn.execute("SELECT real_llm_calls FROM demo_llm_usage WHERE provider = 'gemini'").fetchone()
        call = conn.execute("SELECT * FROM model_calls ORDER BY created_at DESC LIMIT 1").fetchone()
    assert usage["real_llm_calls"] == 5
    assert call["fallback_reason"] == "demo_daily_limit"
    assert call["attempted_provider"] == "gemini"


def test_demo_limit_resets_by_date(tmp_path, monkeypatch):
    _setup_demo(tmp_path, monkeypatch, limit=1)
    monkeypatch.setattr(llm, "GeminiProvider", FakeGeminiProvider)
    monkeypatch.setattr(demo_limits, "utc_day", lambda: "2026-05-04")
    with TestClient(app, base_url="https://testserver") as client:
        first = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()
        second = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()
        monkeypatch.setattr(demo_limits, "utc_day", lambda: "2026-05-05")
        third = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()

    assert first["provider"] == "gemini"
    assert second["fallback_reason"] == "demo_daily_limit"
    assert third["provider"] == "gemini"


def test_provider_health_counts_against_demo_limit(tmp_path, monkeypatch):
    _setup_demo(tmp_path, monkeypatch, limit=1)
    monkeypatch.setattr(llm, "GeminiProvider", FakeGeminiProvider)
    with TestClient(app, base_url="https://testserver") as client:
        first = client.get("/settings/provider-health").json()
        second = client.get("/settings/provider-health").json()

    assert first["status"] == "success"
    assert second["status"] == "fallback_used"
    assert second["fallback_reason"] == "demo_daily_limit"
    assert second["remaining_calls"] == 0


def test_provider_error_fallback_does_not_increment_demo_counter(tmp_path, monkeypatch):
    _setup_demo(tmp_path, monkeypatch)
    monkeypatch.setattr(llm, "GeminiProvider", FailingGeminiProvider)
    with TestClient(app, base_url="https://testserver") as client:
        body = client.post("/chat", json={"message": "What can AgentOS Lite do?"}).json()

    assert body["fallback_reason"] == "provider_error"
    with get_db() as conn:
        usage = conn.execute("SELECT COUNT(*) AS count FROM demo_llm_usage").fetchone()
    assert usage["count"] == 0


def test_ip_fallback_session_is_hashed():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/settings",
            "headers": [(b"x-forwarded-for", b"203.0.113.10")],
            "client": ("198.51.100.1", 12345),
            "server": ("testserver", 443),
            "scheme": "https",
        }
    )
    session_id = demo_limits.fallback_session_id(request)
    assert session_id.startswith("ip_")
    assert "203.0.113.10" not in session_id


def _setup_demo(tmp_path, monkeypatch, limit=5):
    monkeypatch.setenv("AGENTOS_SQLITE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "configured-but-not-used")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-mocked")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("MAX_LLM_CALLS_PER_USER_PER_DAY", str(limit))
    monkeypatch.setenv("DEMO_FALLBACK_TO_MOCK", "true")
    monkeypatch.setenv("LLM_FALLBACK_TO_MOCK", "true")
    get_settings.cache_clear()
    init_db()
    register_tools()
    seed_prompts()
