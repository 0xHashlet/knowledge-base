import uuid

from app.models.document import Document, DocumentVersion, DocumentVersionStatus
from app.models.user import User
from app.services.document_upload_service import DocumentUploadService, UploadDocumentCommand


class FakeStorage:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, object_key: str, data: bytes, content_type: str) -> None:
        self.objects[object_key] = {"data": data, "content_type": content_type}


class FakeRepository:
    def __init__(self):
        self.documents = {}
        self.versions: list[DocumentVersion] = []
        self.current_version_updates = []

    def get_document_by_external_id(self, knowledge_base_id, external_id):
        return self.documents.get((knowledge_base_id, external_id))

    def add_document(self, document):
        self.documents[(document.knowledge_base_id, document.external_id)] = document
        return document

    def next_version_number(self, document_id):
        return len([version for version in self.versions if version.document_id == document_id]) + 1

    def add_version(self, version):
        self.versions.append(version)
        return version

    def set_current_version(self, document, version):
        document.current_version_id = version.id
        self.current_version_updates.append((document.id, version.id))
        return document


class FakeTaskDispatcher:
    def __init__(self):
        self.dispatched = []

    def delay(self, document_version_id):
        self.dispatched.append(document_version_id)


def test_upload_service_creates_document_version_and_stores_object():
    repository = FakeRepository()
    storage = FakeStorage()
    dispatcher = FakeTaskDispatcher()
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")
    service = DocumentUploadService(repository, storage, dispatcher)

    result = service.upload(
        UploadDocumentCommand(
            knowledge_base_id=uuid.uuid4(),
            filename="policy.txt",
            content_type="text/plain",
            content=b"hello",
            uploaded_by=user,
        )
    )

    assert result.document.title == "policy.txt"
    assert result.version.version_number == 1
    assert result.version.status == DocumentVersionStatus.UPLOADED
    assert result.version.storage_path in storage.objects
    assert storage.objects[result.version.storage_path]["data"] == b"hello"
    assert dispatcher.dispatched == [str(result.version.id)]


def test_upload_service_reuses_document_and_increments_version():
    repository = FakeRepository()
    storage = FakeStorage()
    dispatcher = FakeTaskDispatcher()
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")
    service = DocumentUploadService(repository, storage, dispatcher)
    kb_id = uuid.uuid4()

    first = service.upload(
        UploadDocumentCommand(kb_id, "policy.txt", "text/plain", b"v1", user)
    )
    second = service.upload(
        UploadDocumentCommand(kb_id, "policy.txt", "text/plain", b"v2", user)
    )

    assert first.document.id == second.document.id
    assert second.version.version_number == 2
    assert len(repository.versions) == 2
