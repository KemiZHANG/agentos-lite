from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, Field
import os
from dotenv import dotenv_values


def load_environment_files(root_dir: Path | None = None, backend_dir: Path | None = None) -> None:
    """Load root .env then backend/.env while preserving real system env priority."""
    config_path = Path(__file__).resolve()
    backend_dir = backend_dir or config_path.parents[2]
    root_dir = root_dir or config_path.parents[3]
    original_env = dict(os.environ)
    root_values = dotenv_values(root_dir / ".env")
    backend_values = dotenv_values(backend_dir / ".env")
    for key, value in root_values.items():
        if value is not None and key not in original_env:
            os.environ[key] = value
    for key, value in backend_values.items():
        if value is not None and key not in original_env:
            os.environ[key] = value


load_environment_files()


class Settings(BaseModel):
    app_name: str = "AgentOS Lite"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", os.getenv("AGENTOS_ENV", "local")).strip().lower())
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", os.getenv("AGENTOS_ENV", "local")).strip().lower())
    sqlite_path: Path = Field(default_factory=lambda: _sqlite_path())
    cors_origins: list[str] = Field(default_factory=lambda: _cors_origins())
    default_user_id: str = Field(default_factory=lambda: os.getenv("AGENTOS_DEFAULT_USER_ID", "local-user"))
    llm_provider: str = Field(default_factory=lambda: _llm_provider())
    llm_fallback_to_mock: bool = Field(default_factory=lambda: _env_bool("LLM_FALLBACK_TO_MOCK", True))
    gemini_api_key: str | None = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview"))
    embedding_provider: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", os.getenv("AGENTOS_EMBEDDING_PROVIDER", "mock")))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "mock-hash-16"))
    rag_mode: str = Field(default_factory=lambda: os.getenv("RAG_MODE", "local_keyword_mock_embedding"))
    strict_citation_mode: bool = Field(default_factory=lambda: _env_bool("STRICT_CITATION_MODE", True))
    demo_mode: bool = Field(default_factory=lambda: _env_bool("DEMO_MODE", False))
    demo_fallback_to_mock: bool = Field(default_factory=lambda: _env_bool("DEMO_FALLBACK_TO_MOCK", True))
    max_llm_calls_per_user_per_day: int = Field(default_factory=lambda: _env_int("MAX_LLM_CALLS_PER_USER_PER_DAY", _env_int("MAX_LLM_CALLS_PER_DAY", 5)))
    max_llm_calls_per_session: int = Field(default_factory=lambda: _env_int("MAX_LLM_CALLS_PER_SESSION", 20))
    max_llm_calls_per_day: int = Field(default_factory=lambda: _env_int("MAX_LLM_CALLS_PER_DAY", _env_int("MAX_LLM_CALLS_PER_USER_PER_DAY", 5)))

    @property
    def active_model(self) -> str:
        if self.llm_provider == "gemini":
            return self.gemini_model
        return "mock-agentos-lite"

    @property
    def llm_api_key_configured(self) -> bool:
        if self.llm_provider == "gemini":
            return bool(self.gemini_api_key)
        return False

    @property
    def current_mode(self) -> str:
        if self.demo_mode:
            return "hosted_demo"
        if self.llm_provider == "gemini":
            return "local_gemini"
        return "local_mock"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _llm_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", os.getenv("AGENTOS_LLM_PROVIDER", "mock")).strip().lower()
    return provider if provider in {"mock", "gemini"} else "mock"


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


def _sqlite_path() -> Path:
    raw = Path(os.getenv("AGENTOS_SQLITE_PATH", "backend/agentos_lite.db"))
    if raw.is_absolute():
        return raw
    root_dir = Path(__file__).resolve().parents[3]
    return root_dir / raw


@lru_cache
def get_settings() -> Settings:
    return Settings()
