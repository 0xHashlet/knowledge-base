import hashlib
import uuid
from dataclasses import dataclass

from app.models.document import Document, DocumentVersion, DocumentVersionStatus
from app.models.user import User
from app.repositories.documents import DocumentRepository
from app.storage.object_key import build_document_object_key
from app.storage.s3 import create_object_storage


@dataclass(frozen=True)
class UploadDocumentCommand:
    knowledge_base_id: uuid.UUID
    filename: str
    content_type: str
    content: bytes
    uploaded_by: User


@dataclass(frozen=True)
class UploadDocumentResult:
    document: Document
    version: DocumentVersion


class DocumentUploadService:
    supported_content_types = {
        "text/plain",
        "text/markdown",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    def __init__(self, db_or_repository, storage=None, task_dispatcher=None):
        self.repository = db_or_repository
        if not hasattr(db_or_repository, "get_document_by_external_id"):
            self.repository = DocumentRepository(db_or_repository)
        self.storage = storage or create_object_storage()
        if task_dispatcher is None:
            from app.workers.tasks.document_tasks import parse_document_version

            task_dispatcher = parse_document_version
        self.task_dispatcher = task_dispatcher

    def upload(self, command: UploadDocumentCommand) -> UploadDocumentResult:
        if command.content_type not in self.supported_content_types:
            raise ValueError(f"Unsupported document file type: {command.content_type}")

        document = self.repository.get_document_by_external_id(
            command.knowledge_base_id,
            command.filename,
        )
        if document is None:
            document = self.repository.add_document(
                Document(
                    id=uuid.uuid4(),
                    knowledge_base_id=command.knowledge_base_id,
                    title=command.filename,
                    source_type="upload",
                    external_id=command.filename,
                )
            )

        version = DocumentVersion(
            id=uuid.uuid4(),
            document_id=document.id,
            knowledge_base_id=command.knowledge_base_id,
            version_number=self.repository.next_version_number(document.id),
            file_name=command.filename,
            file_type=command.content_type,
            file_size=len(command.content),
            storage_path="",
            content_hash=hashlib.sha256(command.content).hexdigest(),
            status=DocumentVersionStatus.UPLOADED,
            is_latest=True,
            uploaded_by_id=command.uploaded_by.id,
        )
        version.storage_path = build_document_object_key(
            knowledge_base_id=command.knowledge_base_id,
            document_id=document.id,
            version_id=version.id,
            filename=command.filename,
        )
        self.storage.put_object(
            object_key=version.storage_path,
            data=command.content,
            content_type=command.content_type,
        )
        version = self.repository.add_version(version)
        document = self.repository.set_current_version(document, version)
        self.task_dispatcher.delay(str(version.id))
        return UploadDocumentResult(document=document, version=version)
