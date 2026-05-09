import uuid

from app.services.chunk_service import ChunkService
from app.services.document_parser import DocumentParser
from app.vectorstores.base import EmbeddingRecord


class DocumentProcessingService:
    def __init__(
        self,
        repository,
        storage,
        parser: DocumentParser | None = None,
        chunk_service: ChunkService | None = None,
        embedding_service=None,
        embedding_store=None,
        embedding_model: str | None = None,
    ):
        self.repository = repository
        self.storage = storage
        self.parser = parser or DocumentParser()
        self.chunk_service = chunk_service or ChunkService(repository)
        self.embedding_service = embedding_service
        self.embedding_store = embedding_store
        self.embedding_model = embedding_model or "bge-large-zh-v1.5"

    def process_version(self, document_version_id: uuid.UUID | str) -> dict[str, str]:
        version_id = uuid.UUID(str(document_version_id))
        version = self.repository.get_version(version_id)
        if version is None:
            return {"document_version_id": str(document_version_id), "status": "not_found"}

        try:
            self.repository.mark_version_parsing(version)
            content = self.storage.get_object(object_key=version.storage_path)
            parsed = self.parser.parse(file_type=version.file_type, content=content)
            updated_version, chunks = self.chunk_service.store_parsed_text(
                version,
                text=parsed.text,
                parser_name=parsed.parser_name,
                parser_version=parsed.parser_version,
                embedding_model=self.embedding_model,
            )
            self._maybe_embed(chunks)
            return {"document_version_id": str(document_version_id), "status": "parsed"}
        except Exception as exc:
            self.repository.mark_version_failed(version, str(exc))
            return {"document_version_id": str(document_version_id), "status": "failed"}

    def _maybe_embed(self, chunks: list) -> None:
        if not self.embedding_service or not self.embedding_store or not chunks:
            return
        texts = [chunk.content for chunk in chunks]
        vectors = self.embedding_service.embed(texts)
        self.embedding_store.ensure_collection()
        records = [
            EmbeddingRecord(
                chunk_id=chunk.id,
                knowledge_base_id=chunk.knowledge_base_id,
                document_id=chunk.document_id,
                document_version_id=chunk.document_version_id,
                embedding_model=self.embedding_model,
                vector=vec,
            )
            for chunk, vec in zip(chunks, vectors)
        ]
        self.embedding_store.upsert(records)
