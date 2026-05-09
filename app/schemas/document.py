import uuid
from datetime import datetime

from app.models.document import DocumentStatus, DocumentVersionStatus
from app.schemas.common import ApiModel


class DocumentUploadRead(ApiModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    file_name: str
    file_type: str
    file_size: int
    storage_path: str
    status: DocumentVersionStatus


class DocumentVersionRead(ApiModel):
    id: uuid.UUID
    version_number: int
    file_name: str
    file_type: str
    file_size: int
    status: DocumentVersionStatus
    error_message: str | None = None
    created_at: datetime


class DocumentRead(ApiModel):
    id: uuid.UUID
    title: str
    status: DocumentStatus
    current_version: DocumentVersionRead | None = None
