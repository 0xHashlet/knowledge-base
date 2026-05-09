from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.documents import DocumentRepository
from app.services.document_processing_service import DocumentProcessingService
from app.services.embedding_service import create_embedding_service
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
            settings.embedding_endpoint, settings.embedding_model
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
        return svc.process_version(document_version_id)
    finally:
        db.close()
