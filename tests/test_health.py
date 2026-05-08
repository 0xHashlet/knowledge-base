def test_health_endpoint_reports_service_status(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "enterprise-rag-api"}
