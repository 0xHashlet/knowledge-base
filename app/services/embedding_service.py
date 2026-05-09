from __future__ import annotations

from typing import Any


class OpenAICompatibleEmbeddingService:
    """Calls an OpenAI-compatible embedding endpoint (vLLM / Ollama / TEI)."""

    def __init__(self, *, client: Any) -> None:
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._client(texts)


def create_embedding_service(endpoint: str, model: str, api_key: str = "") -> OpenAICompatibleEmbeddingService:
    """Factory for OpenAI-compatible embedding endpoint using httpx."""
    import httpx

    api_base = endpoint.rstrip("/")

    def _embed(texts: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = httpx.post(
            f"{api_base}/embeddings",
            json={"model": model, "input": texts},
            headers=headers,
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        data_sorted = sorted(data, key=lambda d: d["index"])
        return [d["embedding"] for d in data_sorted]

    return OpenAICompatibleEmbeddingService(client=_embed)
