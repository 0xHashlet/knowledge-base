import uuid

from sqlalchemy import select

from app.models.chunk import DocumentChunk
from app.repositories.base import SqlAlchemyRepository


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
                DocumentChunk.content.ilike(f"%{query}%"),
            )
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

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
