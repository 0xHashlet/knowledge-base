from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.documents import DocumentRepository
from app.services.document_processing_service import DocumentProcessingService
from app.services.embedding_service import create_embedding_service
from app.services.notification_service import NotificationService
from app.storage.s3 import create_object_storage
from app.vectorstores.milvus import MilvusEmbeddingStore
from app.workers.celery_app import celery_app


@celery_app.task(name="documents.parse_version")
def parse_document_version(document_version_id: str) -> dict[str, str]:
    settings = get_settings()
    db = SessionLocal()
    repository = DocumentRepository(db)
    try:
        embedding_svc = create_embedding_service(
            settings.embedding_endpoint, settings.embedding_model,
            api_key=settings.embedding_api_key,
        )
        milvus = MilvusEmbeddingStore(
            uri=settings.milvus_uri,
            token=settings.milvus_token,
            collection_name=settings.milvus_collection,
            dimension=settings.vector_dimension,
        )
        svc = DocumentProcessingService(
            repository=repository,
            storage=create_object_storage(),
            embedding_service=embedding_svc,
            embedding_store=milvus,
            embedding_model=settings.embedding_model,
        )
        result = svc.process_version(document_version_id)

        # Send notification on completion or failure
        _notify_if_configured(settings, repository, document_version_id, result)

        return result
    finally:
        db.close()


def _notify_if_configured(settings, repository, document_version_id, result):
    smtp_host = getattr(settings, "smtp_host", None)
    if not smtp_host:
        return
    try:
        import uuid as _uuid
        version = repository.get_version(_uuid.UUID(document_version_id))
        if version is None:
            return
        uploader = getattr(version, "uploaded_by", None)
        to_email = getattr(uploader, "email", None) if uploader else None
        if not to_email:
            return
        notifier = NotificationService(
            smtp_host=smtp_host,
            smtp_port=getattr(settings, "smtp_port", 25),
            smtp_username=getattr(settings, "smtp_username", None),
            smtp_password=getattr(settings, "smtp_password", None),
            smtp_use_tls=getattr(settings, "smtp_use_tls", False),
            sender=getattr(settings, "smtp_sender", "noreply@enterprise-rag.local"),
        )
        if result.get("status") == "parsed":
            notifier.send_document_parsed(
                to_email=to_email,
                document_title=getattr(version, "file_name", ""),
                document_version_id=_uuid.UUID(document_version_id),
            )
        elif result.get("status") == "failed":
            notifier.send_document_failed(
                to_email=to_email,
                document_title=getattr(version, "file_name", ""),
                document_version_id=_uuid.UUID(document_version_id),
                error_message=getattr(version, "error_message", ""),
            )
    except Exception:
        pass  # Notification failure must not affect document processing
