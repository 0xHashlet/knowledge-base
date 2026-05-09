import uuid

from app.models.document import DocumentVersionStatus
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
