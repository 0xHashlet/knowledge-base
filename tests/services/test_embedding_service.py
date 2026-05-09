import pytest
from app.services.embedding_service import OpenAICompatibleEmbeddingService


class FakeEmbeddingClient:
    def __init__(self, embeddings_by_text=None):
        self._embeddings = embeddings_by_text or {}
        self.calls = []

    def embed(self, texts):
        self.calls.append(texts)
        return [self._embeddings.get(t, [0.1, 0.2, 0.3]) for t in texts]


def test_embed_single_text():
    fake = FakeEmbeddingClient({"hello": [0.1, 0.2, 0.3]})
    svc = OpenAICompatibleEmbeddingService(client=fake)
    result = svc.embed(["hello"])
    assert result == [[0.1, 0.2, 0.3]]
    assert len(fake.calls) == 1


def test_embed_multiple_texts():
    fake = FakeEmbeddingClient({"a": [1.0, 0.0], "b": [0.0, 1.0]})
    svc = OpenAICompatibleEmbeddingService(client=fake)
    result = svc.embed(["a", "b"])
    assert len(result) == 2


def test_embed_empty_list():
    fake = FakeEmbeddingClient({})
    svc = OpenAICompatibleEmbeddingService(client=fake)
    assert svc.embed([]) == []
