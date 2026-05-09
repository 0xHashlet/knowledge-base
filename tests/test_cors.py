from app.main import create_app


def test_cors_allows_local_frontend_origin(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_app_registers_cors_middleware():
    app = create_app()

    middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
    assert "CORSMiddleware" in middleware_names
