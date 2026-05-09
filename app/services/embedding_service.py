from __future__ import annotations

from typing import Any


class OpenAICompatibleEmbeddingService:
    """Calls an OpenAI-compatible embedding endpoint (vLLM / Ollama / TEI)."""

    def __init__(self, *, client: Any) -> None:
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._client.embed(texts)


def create_embedding_service(endpoint: str, model: str) -> OpenAICompatibleEmbeddingService:
    """Factory for OpenAI-compatible embedding endpoint using httpx."""
    import httpx

    api_base = endpoint.rstrip("/")

    def _embed(texts: list[str]) -> list[list[float]]:
        resp = httpx.post(
            f"{api_base}/embeddings",
            json={"model": model, "input": texts},
            headers={"Content-Type": "application/json"},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        # Sort by index to preserve input order
        data_sorted = sorted(data, key=lambda d: d["index"])
        return [d["embedding"] for d in data_sorted]

    return OpenAICompatibleEmbeddingService(client=_embed)
