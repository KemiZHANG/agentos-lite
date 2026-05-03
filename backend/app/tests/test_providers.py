import httpx

from app.services.llm import GeminiProvider, get_llm_provider


def test_provider_factory_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("AGENTOS_LLM_PROVIDER", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    provider = get_llm_provider()
    result = provider.generate("hello")
    assert result.provider == "mock"


def test_unknown_provider_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not_supported")
    from app.core.config import get_settings

    get_settings.cache_clear()
    result = get_llm_provider().generate("hello")
    assert result.provider == "mock"


def test_missing_gemini_key_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_FALLBACK_TO_MOCK", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    result = get_llm_provider().generate("hello")
    assert result.provider == "mock"
    assert result.fallback_used is True
    assert "GEMINI_API_KEY" in (result.error or "")


def test_missing_gemini_key_without_fallback_returns_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_FALLBACK_TO_MOCK", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    result = get_llm_provider().generate("hello")
    assert result.provider == "gemini"
    assert result.status == "failed"
    assert "GEMINI_API_KEY" in (result.error or "")


def test_gemini_provider_mocked_http_call():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=secret" in str(request.url)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}],
                "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 3},
            },
        )

    provider = GeminiProvider("secret", "gemini-test", httpx.Client(transport=httpx.MockTransport(handler)))
    result = provider.generate("hello")
    assert result.provider == "gemini"
    assert result.model == "gemini-test"
    assert result.content == "Gemini response"
    assert result.input_tokens == 12

