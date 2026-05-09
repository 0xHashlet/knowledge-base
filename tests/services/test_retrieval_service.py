import uuid

from app.models.chunk import DocumentChunk
from app.models.user import User
from app.services.retrieval_service import RetrievalService
from app.vectorstores.base import EmbeddingSearchResult


class FakePermissionService:
    def __init__(self, allowed_ids):
        self.allowed_ids = allowed_ids
        self.calls = []

    def apply_chunk_scope(self, user, knowledge_base_ids):
        self.calls.append((user, list(knowledge_base_ids)))
        return self.allowed_ids


class FakeChunkRepository:
    def __init__(self):
        self.keyword_calls = []
        self.get_calls = []
        self.keyword_chunks = []
        self.chunks_by_id = {}

    def keyword_search(self, *, query, knowledge_base_ids, limit):
        self.keyword_calls.append(
            {"query": query, "knowledge_base_ids": list(knowledge_base_ids), "limit": limit}
        )
        return self.keyword_chunks

    def get_active_chunks_by_ids(self, chunk_ids):
        self.get_calls.append(list(chunk_ids))
        return [self.chunks_by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in self.chunks_by_id]


class FakeEmbeddingStore:
    def __init__(self):
        self.search_calls = []
        self.results = []

    def search(self, vector, *, limit, knowledge_base_id=None):
        self.search_calls.append(
            {"vector": vector, "limit": limit, "knowledge_base_id": knowledge_base_id}
        )
        return self.results


def _chunk(chunk_id, knowledge_base_id, content):
    return DocumentChunk(
        id=chunk_id,
        knowledge_base_id=knowledge_base_id,
        document_id=uuid.uuid4(),
        document_version_id=uuid.uuid4(),
        chunk_index=0,
        content=content,
        content_hash="hash",
    )


def test_retrieval_filters_permissions_before_recall_and_merges_results():
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")
    allowed_kb_id = uuid.uuid4()
    denied_kb_id = uuid.uuid4()
    keyword_chunk_id = uuid.uuid4()
    vector_chunk_id = uuid.uuid4()
    duplicate_chunk_id = uuid.uuid4()

    repository = FakeChunkRepository()
    repository.keyword_chunks = [
        _chunk(keyword_chunk_id, allowed_kb_id, "keyword hit"),
        _chunk(duplicate_chunk_id, allowed_kb_id, "duplicate from keyword"),
    ]
    repository.chunks_by_id = {
        vector_chunk_id: _chunk(vector_chunk_id, allowed_kb_id, "vector hit"),
        duplicate_chunk_id: _chunk(duplicate_chunk_id, allowed_kb_id, "duplicate from vector"),
    }
    embedding_store = FakeEmbeddingStore()
    embedding_store.results = [
        EmbeddingSearchResult(chunk_id=str(duplicate_chunk_id), score=0.9),
        EmbeddingSearchResult(chunk_id=str(vector_chunk_id), score=0.8),
    ]
    permission_service = FakePermissionService([allowed_kb_id])
    service = RetrievalService(repository, embedding_store, permission_service)

    results = service.retrieve(
        user=user,
        knowledge_base_ids=[allowed_kb_id, denied_kb_id],
        query="policy",
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
    )

    assert permission_service.calls == [(user, [allowed_kb_id, denied_kb_id])]
    assert repository.keyword_calls == [
        {"query": "policy", "knowledge_base_ids": [allowed_kb_id], "limit": 5}
    ]
    assert embedding_store.search_calls == [
        {"vector": [0.1, 0.2, 0.3], "limit": 5, "knowledge_base_id": allowed_kb_id}
    ]
    assert [result.chunk.id for result in results] == [
        keyword_chunk_id,
        duplicate_chunk_id,
        vector_chunk_id,
    ]
    assert [result.source for result in results] == ["keyword", "keyword", "vector"]


def test_retrieval_returns_empty_when_permission_scope_is_empty():
    service = RetrievalService(
        FakeChunkRepository(),
        FakeEmbeddingStore(),
        FakePermissionService([]),
    )

    results = service.retrieve(
        user=User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x"),
        knowledge_base_ids=[uuid.uuid4()],
        query="policy",
        query_vector=[0.1],
    )

    assert results == []
