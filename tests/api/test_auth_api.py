from app.api.deps import get_db
from app.main import create_app


class FakeAuthService:
    def authenticate(self, username_or_email: str, password: str):
        if username_or_email == "alice@example.com" and password == "secret":
            return type("UserObj", (), {"id": "user-1", "is_active": True})()
        return None


def test_login_returns_bearer_token(monkeypatch):
    from app.api.v1 import auth as auth_api

    monkeypatch.setattr(auth_api, "AuthService", lambda db: FakeAuthService())
    app = create_app()
    app.dependency_overrides[get_db] = lambda: object()

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "alice@example.com", "password": "secret"},
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_bad_credentials(monkeypatch):
    from app.api.v1 import auth as auth_api

    monkeypatch.setattr(auth_api, "AuthService", lambda db: FakeAuthService())
    app = create_app()
    app.dependency_overrides[get_db] = lambda: object()

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "alice@example.com", "password": "bad"},
        )

    assert response.status_code == 401
