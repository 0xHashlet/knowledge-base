from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingRecord:
    chunk_id: uuid.UUID
    knowledge_base_id: uuid.UUID
    document_id: uuid.UUID
    document_version_id: uuid.UUID
    embedding_model: str
    vector: list[float]


@dataclass(frozen=True)
class EmbeddingSearchResult:
    chunk_id: str
    score: float


class EmbeddingStore(Protocol):
    def ensure_collection(self) -> None:
        ...

    def upsert(self, records: list[EmbeddingRecord]) -> None:
        ...

    def delete_by_chunk_ids(self, chunk_ids: list[uuid.UUID]) -> None:
        ...

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        knowledge_base_id: uuid.UUID | None = None,
    ) -> list[EmbeddingSearchResult]:
        ...
