import pytest
from app.services.rerank_service import RerankService, RerankCandidate


class FakeRerankClient:
    def __init__(self, scores_by_text=None):
        self._scores = scores_by_text or {}
        self.calls = []

    def rerank(self, query, texts):
        self.calls.append((query, texts))
        return [self._scores.get(t, 0.0) for t in texts]


def test_rerank_sorts_by_score():
    candidates = [
        RerankCandidate(chunk_id="a", content="short"),
        RerankCandidate(chunk_id="b", content="this is longer and more relevant"),
        RerankCandidate(chunk_id="c", content="medium length here"),
    ]
    client = FakeRerankClient({
        "short": 0.3,
        "this is longer and more relevant": 0.9,
        "medium length here": 0.5,
    })
    svc = RerankService(client=client, top_k=2)
    result = svc.rerank(query="test", candidates=candidates)
    assert len(result) == 2
    assert result[0].chunk_id == "b"
    assert result[1].chunk_id == "c"


def test_rerank_empty_candidates():
    svc = RerankService(client=FakeRerankClient(), top_k=10)
    assert svc.rerank("query", []) == []


def test_rerank_fewer_candidates_than_top_k():
    svc = RerankService(client=FakeRerankClient(), top_k=10)
    result = svc.rerank("q", [RerankCandidate(chunk_id="x", content="text")])
    assert len(result) == 1
