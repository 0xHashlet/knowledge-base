from app.main import create_app


def test_phase2_api_routes_are_registered():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/auth/login" in paths
    assert "/api/v1/users" in paths
    assert "/api/v1/users/{user_id}/roles/{role_id}" in paths
    assert "/api/v1/departments" in paths
    assert "/api/v1/roles" in paths
    assert "/api/v1/roles/{role_id}/permissions/{permission_id}" in paths
    assert "/api/v1/permissions" in paths
    assert "/api/v1/knowledge-bases" in paths
    assert "/api/v1/knowledge-bases/{knowledge_base_id}/members" in paths
