import uuid

from sqlalchemy import delete, func, select, update

from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentVersion, DocumentVersionStatus
from app.repositories.base import SqlAlchemyRepository


class DocumentRepository(SqlAlchemyRepository[Document]):
    model = Document

    def get_document_by_external_id(
        self,
        knowledge_base_id: uuid.UUID,
        external_id: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.knowledge_base_id == knowledge_base_id,
            Document.external_id == external_id,
        )
        return self.db.scalars(statement).first()

    def add_document(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def next_version_number(self, document_id: uuid.UUID) -> int:
        statement = select(func.max(DocumentVersion.version_number)).where(
            DocumentVersion.document_id == document_id,
        )
        current = self.db.scalar(statement)
        return int(current or 0) + 1

    def add_version(self, version: DocumentVersion) -> DocumentVersion:
        self.db.execute(
            update(DocumentVersion)
            .where(DocumentVersion.document_id == version.document_id)
            .values(is_latest=False)
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def set_current_version(self, document: Document, version: DocumentVersion) -> Document:
        document.current_version_id = version.id
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_version(self, version_id: uuid.UUID) -> DocumentVersion | None:
        return self.db.get(DocumentVersion, version_id)

    def mark_version_parsing(self, version: DocumentVersion) -> DocumentVersion:
        version.status = DocumentVersionStatus.PARSING
        return self._commit_version(version)

    def mark_version_parsed(
        self,
        version: DocumentVersion,
        raw_text: str,
        parser_name: str,
        parser_version: str,
    ) -> DocumentVersion:
        version.status = DocumentVersionStatus.PARSED
        version.raw_text = raw_text
        version.parser_name = parser_name
        version.parser_version = parser_version
        version.error_message = None
        return self._commit_version(version)

    def mark_version_failed(self, version: DocumentVersion, error_message: str) -> DocumentVersion:
        version.status = DocumentVersionStatus.FAILED
        version.error_message = error_message
        return self._commit_version(version)

    def replace_chunks_for_version(
        self,
        version: DocumentVersion,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_version_id == version.id)
        )
        self.db.add_all(chunks)
        self.db.commit()
        return chunks

    def _commit_version(self, version: DocumentVersion) -> DocumentVersion:
        self.db.commit()
        self.db.refresh(version)
        return version
