def test_health_endpoint_success(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json["data"]
    assert data["status"] == "ok"
    assert data["service"] == "anvaya-api"
    assert data["environment"] == "testing"
    assert data["database"] == "ok"
    assert data["public_demo_enabled"] is False
    assert data["ai_assist_enabled"] is False
    assert data["voice_enabled"] is False
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


def test_health_reports_public_demo_capability(client, app):
    app.config["PUBLIC_DEMO_MODE"] = True
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["data"]["public_demo_enabled"] is True
