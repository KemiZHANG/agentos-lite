from __future__ import annotations

import hashlib
import math
import re

from app.core.config import get_settings


class MockEmbeddingProvider:
    """Deterministic tiny embeddings so local RAG works without API keys."""

    dimensions = 16

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self.dimensions
            vector[index] += 1.0 + (digest[1] / 255.0)
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [round(v / norm, 6) for v in vector]


class OpenAICompatibleEmbeddingProvider:
    """Foundation for future real embeddings; local RAG still uses mock fallback in Phase 2."""

    def __init__(self, base_url: str | None, api_key: str | None, model: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.fallback = MockEmbeddingProvider()

    def embed(self, text: str) -> list[float]:
        return self.fallback.embed(text)


class GeminiEmbeddingProvider:
    """Stub provider kept explicit until Gemini embedding rollout is wired and tested."""

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.fallback = MockEmbeddingProvider()

    def embed(self, text: str) -> list[float]:
        return self.fallback.embed(text)


def get_embedding_provider():
    settings = get_settings()
    if settings.embedding_provider == "openai_compatible":
        return OpenAICompatibleEmbeddingProvider(settings.embedding_base_url, settings.embedding_api_key, settings.embedding_model)
    if settings.embedding_provider == "gemini":
        return GeminiEmbeddingProvider(settings.gemini_api_key, settings.embedding_model)
    return MockEmbeddingProvider()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)
