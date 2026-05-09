import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_permission_service
from app.models.user import User
from app.schemas.document import DocumentUploadRead
from app.services.document_upload_service import DocumentUploadService, UploadDocumentCommand
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/knowledge-bases/{knowledge_base_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> DocumentUploadRead:
    if not permission_service.can_access_knowledge_base(current_user, knowledge_base_id):
        raise HTTPException(status_code=403, detail="Knowledge base access denied")

    content = await file.read()
    try:
        result = DocumentUploadService(db).upload(
            UploadDocumentCommand(
                knowledge_base_id=knowledge_base_id,
                filename=file.filename or "document",
                content_type=file.content_type or "application/octet-stream",
                content=content,
                uploaded_by=current_user,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DocumentUploadRead(
        document_id=result.document.id,
        version_id=result.version.id,
        version_number=result.version.version_number,
        file_name=result.version.file_name,
        file_type=result.version.file_type,
        file_size=result.version.file_size,
        storage_path=result.version.storage_path,
        status=result.version.status,
    )
