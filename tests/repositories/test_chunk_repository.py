import uuid

from app.models.chunk import DocumentChunk
from app.repositories.chunks import ChunkRepository


def test_chunk_repository_keyword_search_builds_permission_scoped_statement():
    class FakeScalars:
        def all(self):
            return []

    class FakeDb:
        def __init__(self):
            self.statement = None

        def scalars(self, statement):
            self.statement = statement
            return FakeScalars()

    db = FakeDb()
    kb_id = uuid.uuid4()
    repository = ChunkRepository(db)

    assert repository.keyword_search(query="policy", knowledge_base_ids=[kb_id], limit=10) == []

    compiled = str(db.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "document_chunks" in compiled
    assert "lower(document_chunks.content) LIKE lower('%policy%')" in compiled
    assert kb_id.hex in compiled
    assert "document_chunks.is_active IS true" in compiled


def test_chunk_repository_returns_no_chunks_for_empty_id_list():
    class FakeDb:
        def scalars(self, statement):
            raise AssertionError("database should not be queried")

    assert ChunkRepository(FakeDb()).get_active_chunks_by_ids([]) == []
