def test_health_endpoint_success(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["data"] == {"status": "ok", "service": "anvaya-api", "environment": "testing", "database": "ok"}
    assert response.json["warnings"] == []
    assert response.json["request_id"] == response.headers["X-Request-ID"]


def test_request_id_is_propagated(client):
    response = client.get("/api/health", headers={"X-Request-ID": "foundation-test-001"})
    assert response.headers["X-Request-ID"] == "foundation-test-001"
    assert response.json["request_id"] == "foundation-test-001"


def test_invalid_request_id_is_replaced(client):
    response = client.get("/api/health", headers={"X-Request-ID": "not valid"})
    assert response.json["request_id"] != "not valid"
    assert response.headers["X-Request-ID"] == response.json["request_id"]
