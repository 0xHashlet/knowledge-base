import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api import deps as api_deps
from app.main import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


class _MockDb:
    """Minimal mock DB session for testing API routes."""

    def __init__(self, get_return=None):
        self._get_return = get_return
        self.added = []
        self.committed = False
        self.refreshed = []

    def get(self, model, ident):
        return self._get_return

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.committed = True

    def refresh(self, instance):
        self.refreshed.append(instance)

    def close(self):
        pass


def _fake_current_user():
    return type("UserObj", (), {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
        "is_superuser": False,
    })()


@pytest.fixture()
def auth_client():
    mock_db = _MockDb()
    app = create_app()
    app.dependency_overrides[api_deps.get_current_user] = _fake_current_user
    app.dependency_overrides[api_deps.get_db] = lambda: mock_db
    with TestClient(app) as test_client:
        yield test_client
