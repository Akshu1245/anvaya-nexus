from backend.anvaya.services.generator import generate


def _investigation(client):
    client.post(
        "/api/auth/login",
        json={
            "username": "investigator.demo",
            "password": client.application.config["DEMO_PASSWORD"],
        },
    )
    return client.post(
        "/api/investigations",
        json={
            "title": "Aggregate trends test",
            "purpose": "Active Case Investigation",
            "selected_sources": ["CCTNS_REPLICA"],
        },
    ).get_json()["data"]


def test_trends_are_deterministic_aggregate_and_non_predictive(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    response = client.get(
        f"/api/investigations/{investigation['id']}/analytics/trends"
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["summary"]["authorised_case_count"] > 0
    assert data["monthly_incidents"]
    assert data["station_hotspots"]
    assert "hotspot_deltas" in data
    assert "volume_anomalies" in data
    assert data["methodology"]["small_cell_threshold"] == 2
    limitations = " ".join(data["methodology"]["limitations"]).lower()
    assert "not a crime forecast" in limitations
    assert "protected demographic" in limitations
    assert all(item["count"] >= 2 for item in data["station_hotspots"])


def test_trends_require_owned_investigation(client, app):
    generate(app.extensions["repository"], app.config, "test")
    _investigation(client)
    response = client.get("/api/investigations/SYN-INV-MISSING/analytics/trends")
    assert response.status_code == 404


def test_shift_briefing_is_deterministic_and_non_predictive(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    first = client.get(f"/api/investigations/{investigation['id']}/analytics/briefing")
    second = client.get(f"/api/investigations/{investigation['id']}/analytics/briefing")
    assert first.status_code == 200
    assert first.get_json()["data"] == second.get_json()["data"]
    data = first.get_json()["data"]
    assert data["summary"]["authorised_case_count"] > 0
    assert data["human_review_required"] is True
    blob = str(data).lower()
    assert "arrest recommendation" not in blob or "no" in blob
    assert data["human_review_required"] is True
    assert any("not predictive" in item.lower() or "not a crime forecast" in item.lower() for item in data["limitations"] + data["trends"]["methodology"]["limitations"])
    assert any("person-risk" in item.lower() or "risk score" in item.lower() for item in data["limitations"])
    assert "scoring" not in data.get("trends", {}).get("methodology", {}).get("method", "").lower()


def test_case_compare_and_priorities_are_factual_only(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    compare = client.get(
        f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/compare/SYN-CASE-0002"
    )
    assert compare.status_code == 200
    payload = compare.get_json()["data"]
    assert payload["left"]["case_id"] == "SYN-CASE-0001"
    assert payload["right"]["case_id"] == "SYN-CASE-0002"
    assert payload["metadata"]["scoring"] is False
    assert "risk score" not in str(payload).lower()
    assert any("guilt" in item.lower() for item in payload["limitations"])
    assert any("does not establish" in item.lower() or "not establish" in item.lower() for item in payload["limitations"])
    priorities = client.get(
        f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/priorities"
    )
    assert priorities.status_code == 200
    cards = priorities.get_json()["data"]
    assert "priorities" in cards
    assert "not a legal direction" in " ".join(cards["limitations"]).lower()
