from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RerankCandidate:
    chunk_id: str
    content: str


class RerankService:
    """Cross-encoder reranker for improving retrieval precision."""

    def __init__(self, *, client, top_k: int = 5) -> None:
        self._client = client
        self.top_k = top_k

    def rerank(self, query: str, candidates: list[RerankCandidate]) -> list[RerankCandidate]:
        if not candidates:
            return []
        texts = [c.content for c in candidates]
        scores = self._client(query, texts)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        top = ranked[: self.top_k]
        return [c for c, _ in top]


def create_rerank_service(endpoint: str, model: str, top_k: int = 5, api_key: str = "") -> RerankService:
    """Factory for an OpenAI-compatible rerank endpoint using httpx."""
    import httpx

    api_base = endpoint.rstrip("/")

    def _rerank(query: str, texts: list[str]) -> list[float]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = httpx.post(
            f"{api_base}/rerank",
            json={"model": model, "query": query, "documents": texts},
            headers=headers,
            timeout=60.0,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        sorted_results = sorted(results, key=lambda r: r.get("index", 0))
        return [r.get("relevance_score", 0.0) for r in sorted_results]

    return RerankService(client=_rerank, top_k=top_k)
