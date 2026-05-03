import httpx

from app.services.llm import GeminiProvider, OpenAICompatibleProvider, get_llm_provider


def test_provider_factory_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("AGENTOS_LLM_PROVIDER", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    provider = get_llm_provider()
    result = provider.generate("hello")
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


def test_openai_compatible_provider_mocked_http_call():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://local.test/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "OpenAI-compatible response"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4},
            },
        )

    provider = OpenAICompatibleProvider(
        "http://local.test/v1",
        "test-key",
        "test-model",
        httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = provider.generate("hello")
    assert result.provider == "openai_compatible"
    assert result.model == "test-model"
    assert result.content == "OpenAI-compatible response"
    assert result.output_tokens == 4

