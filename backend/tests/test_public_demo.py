def test_public_demo_is_explicitly_gated_and_uses_normal_session_controls(client, app):
    denied = client.post("/api/auth/public-demo")
    assert denied.status_code == 404

    app.config["PUBLIC_DEMO_MODE"] = True
    response = client.post("/api/auth/public-demo")
    assert response.status_code == 200
    assert response.json["data"]["role"] == "INVESTIGATOR"
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert client.get("/api/auth/session").status_code == 200


def test_public_demo_respects_login_rate_limit(client, app):
    app.config["PUBLIC_DEMO_MODE"] = True
    app.config["LOGIN_RATE_LIMIT_PER_MINUTE"] = 1
    assert client.post("/api/auth/public-demo").status_code == 200
    assert client.post("/api/auth/public-demo").status_code == 429
