import uuid

import pytest


def test_submit_feedback_requires_auth(client):
    resp = client.post("/api/v1/feedback", json={
        "message_id": str(uuid.uuid4()),
        "rating": "up",
    })
    assert resp.status_code == 401


def test_submit_feedback_invalid_message_id_format(auth_client):
    resp = auth_client.post("/api/v1/feedback", json={
        "message_id": "not-a-uuid",
        "rating": "up",
    })
    assert resp.status_code == 400


def test_submit_feedback_invalid_rating(auth_client):
    resp = auth_client.post("/api/v1/feedback", json={
        "message_id": str(uuid.uuid4()),
        "rating": "bad",
    })
    assert resp.status_code == 400


def test_feedback_route_is_registered(client):
    """Verify the feedback endpoint is registered in the app."""
    from app.api.v1.router import api_router
    routes = [r.path for r in api_router.routes]
    assert "/feedback" in routes
