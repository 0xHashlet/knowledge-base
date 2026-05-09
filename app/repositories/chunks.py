import uuid

from sqlalchemy import select

from app.models.chunk import DocumentChunk
from app.repositories.base import SqlAlchemyRepository
from app.services.bm25_service import Bm25SearchService, SearchableChunk


class ChunkRepository(SqlAlchemyRepository[DocumentChunk]):
    model = DocumentChunk

    def keyword_search(
        self,
        *,
        query: str,
        knowledge_base_ids: list[uuid.UUID],
        limit: int = 10,
    ) -> list[DocumentChunk]:
        if not knowledge_base_ids:
            return []
        statement = (
            select(DocumentChunk)
            .where(
                DocumentChunk.is_active.is_(True),
                DocumentChunk.knowledge_base_id.in_(knowledge_base_ids),
            )
        )
        all_chunks = list(self.db.scalars(statement).all())
        searchable = [
            SearchableChunk(chunk_id=str(c.id), content=c.content) for c in all_chunks
        ]
        bm25 = Bm25SearchService(searchable)
        results = bm25.search(query, limit=limit)
        chunk_by_id = {c.id: c for c in all_chunks}
        return [chunk_by_id[uuid.UUID(r.chunk_id)] for r in results if uuid.UUID(r.chunk_id) in chunk_by_id]

    def get_active_chunks_by_ids(self, chunk_ids: list[uuid.UUID]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        statement = select(DocumentChunk).where(
            DocumentChunk.is_active.is_(True),
            DocumentChunk.id.in_(chunk_ids),
        )
        chunks = list(self.db.scalars(statement).all())
        chunks_by_id = {chunk.id: chunk for chunk in chunks}
        return [chunks_by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks_by_id]
