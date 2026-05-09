import uuid

from app.services.chunk_service import ChunkService
from app.services.document_parser import DocumentParser


class DocumentProcessingService:
    def __init__(
        self,
        repository,
        storage,
        parser: DocumentParser | None = None,
        chunk_service: ChunkService | None = None,
    ):
        self.repository = repository
        self.storage = storage
        self.parser = parser or DocumentParser()
        self.chunk_service = chunk_service or ChunkService(repository)

    def process_version(self, document_version_id: uuid.UUID | str) -> dict[str, str]:
        version_id = uuid.UUID(str(document_version_id))
        version = self.repository.get_version(version_id)
        if version is None:
            return {"document_version_id": str(document_version_id), "status": "not_found"}

        try:
            self.repository.mark_version_parsing(version)
            content = self.storage.get_object(object_key=version.storage_path)
            parsed = self.parser.parse(file_type=version.file_type, content=content)
            self.chunk_service.store_parsed_text(
                version,
                text=parsed.text,
                parser_name=parsed.parser_name,
                parser_version=parsed.parser_version,
            )
            return {"document_version_id": str(document_version_id), "status": "parsed"}
        except Exception as exc:
            self.repository.mark_version_failed(version, str(exc))
            return {"document_version_id": str(document_version_id), "status": "failed"}
