from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings, load_environment_files
from app.main import app
from app.services import llm
from app.services.llm import ModelResult


def test_backend_env_overrides_root_env_without_overriding_system_env(tmp_path, monkeypatch):
    root_dir = tmp_path / "repo"
    backend_dir = root_dir / "backend"
    backend_dir.mkdir(parents=True)
    (root_dir / ".env").write_text("LLM_PROVIDER=mock\nGEMINI_MODEL=root-model\n", encoding="utf-8")
    (backend_dir / ".env").write_text("LLM_PROVIDER=gemini\nGEMINI_MODEL=backend-model\n", encoding="utf-8")

    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    load_environment_files(root_dir=Path(root_dir), backend_dir=Path(backend_dir))
    assert get_settings.cache_clear() is None
    settings = get_settings()
    assert settings.llm_provider == "gemini"
    assert settings.gemini_model == "backend-model"

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("GEMINI_MODEL", "system-model")
    load_environment_files(root_dir=Path(root_dir), backend_dir=Path(backend_dir))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.llm_provider == "mock"
    assert settings.active_model == "mock-agentos-lite"
    assert settings.gemini_model == "system-model"


def test_settings_api_does_not_expose_secret(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    get_settings.cache_clear()

    response = TestClient(app).get("/settings")
    body = response.json()
    serialized = str(body)
    assert response.status_code == 200
    assert body["llm_provider"] == "gemini"
    assert body["active_model"] == "gemini-test"
    assert body["llm_api_key_configured"] is True
    assert "super-secret-test-key" not in serialized


def test_provider_health_mock_does_not_call_external(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()

    response = TestClient(app).get("/settings/provider-health")
    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert body["status"] == "success"
    assert body["fallback_used"] is False


def test_provider_health_gemini_uses_mocked_provider(monkeypatch):
    class FakeGeminiProvider:
        provider = "gemini"
        model = "gemini-mocked"

        def __init__(self, api_key, model):
            self.api_key = api_key
            self.model = model

        def generate(self, prompt, *, task_type="general_chat", context=None):
            return ModelResult(
                content="ok",
                input_tokens=1,
                output_tokens=1,
                latency_ms=5,
                provider="gemini",
                model=self.model,
            )

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "configured-but-not-used")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-mocked")
    monkeypatch.setattr(llm, "GeminiProvider", FakeGeminiProvider)
    get_settings.cache_clear()

    response = TestClient(app).get("/settings/provider-health")
    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "gemini"
    assert body["model"] == "gemini-mocked"
    assert body["status"] == "success"
    assert body["fallback_used"] is False
    assert "configured-but-not-used" not in str(body)


def test_fallback_to_mock_reason_for_missing_gemini_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_FALLBACK_TO_MOCK", "true")
    get_settings.cache_clear()

    result = llm.get_llm_provider().generate("hello")
    assert result.provider == "mock"
    assert result.fallback_used is True
    assert result.fallback_reason == "missing_key"
