from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.documents import DocumentRepository
from app.services.document_processing_service import DocumentProcessingService
from app.storage.s3 import create_object_storage


@celery_app.task(name="documents.parse_version")
def parse_document_version(document_version_id: str) -> dict[str, str]:
    db = SessionLocal()
    repository = DocumentRepository(db)
    try:
        return DocumentProcessingService(repository, create_object_storage()).process_version(
            document_version_id
        )
    finally:
        db.close()
