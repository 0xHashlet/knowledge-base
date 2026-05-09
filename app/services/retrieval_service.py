import uuid
from dataclasses import dataclass

from app.models.chunk import DocumentChunk
from app.models.user import User
from app.services.rerank_service import RerankCandidate


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    source: str
    score: float | None = None


class RetrievalService:
    def __init__(self, chunk_repository, embedding_store, permission_service,
                 rerank_service=None):
        self.chunk_repository = chunk_repository
        self.embedding_store = embedding_store
        self.permission_service = permission_service
        self.rerank_service = rerank_service

    def retrieve(
        self,
        *,
        user: User,
        knowledge_base_ids: list[uuid.UUID],
        query: str,
        query_vector: list[float] | None = None,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        allowed_kb_ids = self.permission_service.apply_chunk_scope(user, knowledge_base_ids)
        if not allowed_kb_ids:
            return []

        merged: list[RetrievalResult] = []
        seen_chunk_ids: set[uuid.UUID] = set()

        keyword_chunks = self.chunk_repository.keyword_search(
            query=query,
            knowledge_base_ids=allowed_kb_ids,
            limit=limit,
        )
        for chunk in keyword_chunks:
            if chunk.id not in seen_chunk_ids:
                merged.append(RetrievalResult(chunk=chunk, source="keyword"))
                seen_chunk_ids.add(chunk.id)

        if query_vector:
            vector_hits = self._vector_search(query_vector, allowed_kb_ids, limit)
            vector_chunk_ids = [
                uuid.UUID(hit.chunk_id)
                for hit in vector_hits
                if uuid.UUID(hit.chunk_id) not in seen_chunk_ids
            ]
            chunks_by_id = {
                chunk.id: chunk for chunk in self.chunk_repository.get_active_chunks_by_ids(vector_chunk_ids)
            }
            scores_by_id = {uuid.UUID(hit.chunk_id): hit.score for hit in vector_hits}
            for chunk_id in vector_chunk_ids:
                chunk = chunks_by_id.get(chunk_id)
                if chunk is None:
                    continue
                merged.append(
                    RetrievalResult(
                        chunk=chunk,
                        source="vector",
                        score=scores_by_id.get(chunk_id),
                    )
                )
                seen_chunk_ids.add(chunk_id)

        if self.rerank_service and merged:
            candidates = [
                RerankCandidate(chunk_id=str(r.chunk.id), content=r.chunk.content)
                for r in merged
            ]
            reranked = self.rerank_service.rerank(query, candidates)
            reranked_ids = {r.chunk_id for r in reranked}
            merged = [r for r in merged if str(r.chunk.id) in reranked_ids]

        return merged[:limit]

    def _vector_search(self, query_vector: list[float], allowed_kb_ids: list[uuid.UUID], limit: int):
        results = []
        for knowledge_base_id in allowed_kb_ids:
            results.extend(
                self.embedding_store.search(
                    query_vector,
                    limit=limit,
                    knowledge_base_id=knowledge_base_id,
                )
            )
        return results
