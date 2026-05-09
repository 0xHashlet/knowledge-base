from __future__ import annotations

from dataclasses import dataclass

import jieba
from rank_bm25 import BM25Okapi


@dataclass(frozen=True)
class SearchableChunk:
    chunk_id: str
    content: str


class Bm25SearchService:
    def __init__(self, chunks: list[SearchableChunk]) -> None:
        self._chunks = chunks
        self._chunk_map = {c.chunk_id: c for c in chunks}
        self._tokenized = [list(jieba.cut(c.content)) for c in chunks]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    def search(self, query: str, limit: int = 10) -> list[SearchableChunk]:
        if not self._bm25:
            return []
        tokenized_query = list(jieba.cut(query))
        scores = self._bm25.get_scores(tokenized_query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:limit]
        return [self._chunks[i] for i, score in ranked if score > 0]
