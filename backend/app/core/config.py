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
    llm_provider: str = Field(default_factory=lambda: os.getenv("AGENTOS_LLM_PROVIDER", "mock"))
    embedding_provider: str = Field(default_factory=lambda: os.getenv("AGENTOS_EMBEDDING_PROVIDER", "mock"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
