from app.workers.celery_app import celery_app


@celery_app.task(name="documents.parse_version")
def parse_document_version(document_version_id: str) -> dict[str, str]:
    return {
        "document_version_id": document_version_id,
        "status": "queued",
    }
