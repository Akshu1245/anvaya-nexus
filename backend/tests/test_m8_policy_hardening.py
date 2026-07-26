import json

from backend.anvaya.services.generator import generate
from backend.anvaya.services.policy import evaluate


def _login(client, app, username="investigator.demo"):
    return client.post("/api/auth/login", json={"username": username, "password": app.config["DEMO_PASSWORD"]})


def _investigation(client, purpose="Active Case Investigation", sources=("CCTNS_REPLICA",)):
    return client.post("/api/investigations", json={
        "title": "Synthetic policy verification", "purpose": purpose, "selected_sources": list(sources),
    })


def test_missing_and_unknown_role_context_fail_closed():
    missing = evaluate({}, "Active Case Investigation", ["CCTNS_REPLICA"], "SEARCH")
    unknown = evaluate({"role": "UNKNOWN"}, "Active Case Investigation", ["CCTNS_REPLICA"], "SEARCH")
    assert not missing.allowed and missing.denial_code == "INVALID_ROLE_CONTEXT"
    assert not unknown.allowed and unknown.denial_code == "INVALID_ROLE_CONTEXT"


def test_missing_and_invalid_purpose_fail_closed_on_alternate_routes(client, app):
    generate(app.extensions["repository"], app.config, "test")
    _login(client, app)
    for url in (
        "/api/source-control",
        "/api/cases/SYN-CASE-0001/360",
        "/api/source-passports/SYN-SR-CCTNS_REPLICA-SYN-CASE-0001",
        "/api/m5/graph/SYN-CASE-0001",
        "/api/m5/assurance/SYN-CASE-0001",
    ):
        response = client.get(url)
        assert response.status_code == 403
        assert response.get_json()["code"] == "INVALID_PURPOSE"
        assert "Traceback" not in response.get_data(as_text=True)
    invalid = client.get("/api/cases/SYN-CASE-0001/360?purpose=Not%20Approved")
    assert invalid.status_code == 403 and invalid.get_json()["code"] == "INVALID_PURPOSE"


def test_external_case_and_brief_mask_narrative_people_coordinates_and_evidence(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    _login(client, app)
    investigation = _investigation(client).get_json()["data"]
    raw_case = repository.find_case_360_case("SYN-CASE-0002")
    raw_people = [row["display_name"] for row in repository.list_case_people("SYN-CASE-0002", ("CCTNS_REPLICA",))]

    case_response = client.get("/api/cases/SYN-CASE-0002/360?purpose=Active%20Case%20Investigation")
    assert case_response.status_code == 200
    detail = case_response.get_json()["data"]
    serialized = json.dumps(detail)
    assert detail["overview"]["masking"]["level"] == "EXTERNAL"
    assert detail["incident"]["brief_facts"] == "Masked by policy."
    assert detail["incident"]["brief_facts_masked"] is True
    assert detail["incident"]["latitude"] is None and detail["incident"]["longitude"] is None
    assert raw_case["brief_facts"] not in serialized
    assert all(name not in serialized for name in raw_people)
    assert all(record["sensitive_evidence_reference"]["status"] for record in detail["evidence"])

    brief = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0002/brief").get_json()["data"]
    brief_text = json.dumps(brief)
    assert brief["policy"]["masking"]["level"] == "EXTERNAL"
    assert raw_case["brief_facts"] not in brief_text
    assert all(name not in brief_text for name in raw_people)


def test_analyst_is_masked_and_cannot_use_supervisor_or_investigator_views(client, app):
    generate(app.extensions["repository"], app.config, "test")
    _login(client, app, "analyst.demo")
    investigation = _investigation(client, "Pattern Research").get_json()["data"]
    plan = {"intent": "SEARCH", "filters": {"case_identifier": "SYN-FIR-000001"}, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 25, "confidence": 1, "uncertain_fields": [], "protected_tokens": [], "requires_confirmation": False}
    result = client.post(f"/api/investigations/{investigation['id']}/search", json=plan).get_json()["data"]["results"][0]
    assert result["masking"]["level"] == "ANALYST"
    assert _investigation(client, "Active Case Investigation").status_code == 403
    assert _investigation(client, "Supervisor Review", ()).status_code == 403


def test_denied_and_masked_case_access_are_audited_safely(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    _login(client, app)
    assert _investigation(client, sources=("COURT_REPLICA",)).status_code == 403
    assert client.get("/api/cases/SYN-CASE-0002/360?purpose=Active%20Case%20Investigation").status_code == 200
    denials = repository.connection.execute("SELECT safe_metadata_json FROM audit_events WHERE event_type='PERMISSION_DENIAL'").fetchall()
    views = repository.connection.execute("SELECT safe_metadata_json FROM audit_events WHERE event_type='CASE_360_OPENED'").fetchall()
    assert denials and all("password" not in row[0].lower() and "token" not in row[0].lower() for row in denials)
    assert any(json.loads(row[0]).get("masking_level") == "EXTERNAL" for row in views)


def test_source_restrictions_and_missing_session_are_safe(client, app):
    assert client.get("/api/source-control?purpose=Active%20Case%20Investigation").status_code == 401
    _login(client, app)
    denied = _investigation(client, sources=("PROSECUTION_REPLICA",))
    assert denied.status_code == 403
    assert denied.get_json() == {
        "request_id": denied.get_json()["request_id"], "code": "SOURCE_DENIED",
        "message": "One or more sources are unavailable or not permitted.", "retryable": False,
    }
