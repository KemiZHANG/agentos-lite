from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    app_name: str = "AgentOS Lite"
    environment: str = Field(default_factory=lambda: os.getenv("AGENTOS_ENV", "local"))
    sqlite_path: Path = Field(default_factory=lambda: Path(os.getenv("AGENTOS_SQLITE_PATH", "backend/agentos_lite.db")))
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    default_user_id: str = Field(default_factory=lambda: os.getenv("AGENTOS_DEFAULT_USER_ID", "local-user"))
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", os.getenv("AGENTOS_LLM_PROVIDER", "mock")))
    llm_fallback_to_mock: bool = Field(default_factory=lambda: _env_bool("LLM_FALLBACK_TO_MOCK", True))
    gemini_api_key: str | None = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview"))
    llm_base_url: str | None = Field(default_factory=lambda: os.getenv("LLM_BASE_URL"))
    llm_api_key: str | None = Field(default_factory=lambda: os.getenv("LLM_API_KEY"))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "mock-agentos-lite"))
    embedding_provider: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", os.getenv("AGENTOS_EMBEDDING_PROVIDER", "mock")))
    embedding_base_url: str | None = Field(default_factory=lambda: os.getenv("EMBEDDING_BASE_URL"))
    embedding_api_key: str | None = Field(default_factory=lambda: os.getenv("EMBEDDING_API_KEY"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "mock-hash-16"))
    rag_mode: str = Field(default_factory=lambda: os.getenv("RAG_MODE", "local_keyword_mock_embedding"))
    strict_citation_mode: bool = Field(default_factory=lambda: _env_bool("STRICT_CITATION_MODE", True))

    @property
    def active_model(self) -> str:
        if self.llm_provider == "gemini":
            return self.gemini_model
        if self.llm_provider == "openai_compatible":
            return self.llm_model
        return "mock-agentos-lite"

    @property
    def llm_api_key_configured(self) -> bool:
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key)
        if self.llm_provider == "openai_compatible":
            return bool(self.llm_api_key)
        return False


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
