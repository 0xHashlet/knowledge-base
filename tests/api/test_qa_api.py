import uuid


def test_qa_ask_requires_auth(client):
    resp = client.post("/api/v1/qa/ask", json={
        "question": "年假多少天",
        "knowledge_base_ids": [str(uuid.uuid4())],
    })
    assert resp.status_code == 401


def test_qa_route_is_registered(client):
    from app.api.v1.router import api_router
    routes = [r.path for r in api_router.routes]
    assert any("/qa/ask" in r for r in routes)
