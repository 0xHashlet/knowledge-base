from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from app.vectorstores.base import EmbeddingRecord, EmbeddingSearchResult


class MilvusEmbeddingStore:
    def __init__(
        self,
        *,
        uri: str,
        token: str | None,
        collection_name: str,
        dimension: int,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.collection_name = collection_name
        self.dimension = dimension
        self.client = self._build_client(uri, token, client_factory)

    def ensure_collection(self) -> None:
        if not self.client.has_collection(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                schema=self._build_schema(),
                index_params=self._build_index_params(),
            )
        self.client.load_collection(self.collection_name)

    def upsert(self, records: list[EmbeddingRecord]) -> None:
        if not records:
            return
        self.client.upsert(
            collection_name=self.collection_name,
            data=[self._serialize_record(record) for record in records],
        )

    def delete_by_chunk_ids(self, chunk_ids: list[uuid.UUID]) -> None:
        if not chunk_ids:
            return
        quoted_ids = ", ".join(f'"{chunk_id}"' for chunk_id in chunk_ids)
        self.client.delete(
            collection_name=self.collection_name,
            filter=f"chunk_id in [{quoted_ids}]",
        )

    def search(
        self,
        vector: list[float],
        *,
        limit: int,
        knowledge_base_id: uuid.UUID | None = None,
    ) -> list[EmbeddingSearchResult]:
        filter_expression = None
        if knowledge_base_id is not None:
            filter_expression = f'knowledge_base_id == "{knowledge_base_id}"'
        raw_results = self.client.search(
            collection_name=self.collection_name,
            data=[vector],
            limit=limit,
            filter=filter_expression,
        )
        return [
            EmbeddingSearchResult(
                chunk_id=str(hit.get("entity", {}).get("chunk_id", hit.get("id"))),
                score=float(hit.get("distance", 0)),
            )
            for hit in raw_results[0]
        ]

    @staticmethod
    def _build_client(
        uri: str,
        token: str | None,
        client_factory: Callable[..., Any] | None,
    ) -> Any:
        if client_factory is None:
            from pymilvus import MilvusClient

            client_factory = MilvusClient
        return client_factory(uri=uri, token=token)

    def _build_schema(self) -> Any:
        from pymilvus import DataType, MilvusClient

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=64)
        schema.add_field("chunk_id", DataType.VARCHAR, max_length=64)
        schema.add_field("knowledge_base_id", DataType.VARCHAR, max_length=64)
        schema.add_field("document_id", DataType.VARCHAR, max_length=64)
        schema.add_field("document_version_id", DataType.VARCHAR, max_length=64)
        schema.add_field("embedding_model", DataType.VARCHAR, max_length=120)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.dimension)
        return schema

    def _build_index_params(self) -> Any:
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )
        return index_params

    @staticmethod
    def _serialize_record(record: EmbeddingRecord) -> dict[str, Any]:
        return {
            "id": str(record.chunk_id),
            "chunk_id": str(record.chunk_id),
            "knowledge_base_id": str(record.knowledge_base_id),
            "document_id": str(record.document_id),
            "document_version_id": str(record.document_version_id),
            "embedding_model": record.embedding_model,
            "vector": record.vector,
        }
