import uuid

from app.api.deps import get_current_user, get_db, get_permission_service
from app.main import create_app
from app.models.user import User


def test_document_upload_route_is_registered():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/knowledge-bases/{knowledge_base_id}/documents" in paths


def test_document_upload_requires_authentication(client):
    response = client.post(
        f"/api/v1/knowledge-bases/{uuid.uuid4()}/documents",
        files={"file": ("policy.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 401


def test_document_upload_rejects_non_member(monkeypatch):
    from fastapi.testclient import TestClient

    app = create_app()
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")

    class FakePermissionService:
        def can_access_knowledge_base(self, current_user, knowledge_base_id):
            return False

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_permission_service] = lambda: FakePermissionService()
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/knowledge-bases/{uuid.uuid4()}/documents",
            files={"file": ("policy.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 403


def test_document_upload_returns_document_version(monkeypatch):
    from fastapi.testclient import TestClient
    from app.api.v1 import documents as documents_api

    app = create_app()
    kb_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()

    class FakePermissionService:
        def can_access_knowledge_base(self, current_user, knowledge_base_id):
            return current_user is user and knowledge_base_id == kb_id

    class FakeUploadResult:
        document = type("DocumentObj", (), {"id": document_id, "title": "policy.txt"})()
        version = type(
            "VersionObj",
            (),
            {
                "id": version_id,
                "document_id": document_id,
                "knowledge_base_id": kb_id,
                "version_number": 1,
                "file_name": "policy.txt",
                "file_type": "text/plain",
                "file_size": 5,
                "storage_path": "knowledge-bases/kb/documents/doc/versions/v/source/policy.txt",
                "status": "uploaded",
            },
        )()

    class FakeUploadService:
        def __init__(self, db):
            pass

        def upload(self, command):
            assert command.knowledge_base_id == kb_id
            assert command.content == b"hello"
            assert command.uploaded_by is user
            return FakeUploadResult()

    monkeypatch.setattr(documents_api, "DocumentUploadService", FakeUploadService)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_permission_service] = lambda: FakePermissionService()
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            files={"file": ("policy.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 201
    assert response.json()["document_id"] == str(document_id)
    assert response.json()["version_id"] == str(version_id)
    assert response.json()["version_number"] == 1
