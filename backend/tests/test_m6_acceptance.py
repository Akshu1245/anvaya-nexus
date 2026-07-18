"""Deterministic M6 acceptance path using verified M2 synthetic identifiers."""

from backend.anvaya.services.generator import generate

PASSWORD = "ANVAYA-DEMO-ONLY-2026"
GOLDEN_FIR = "SYN-FIR-000001"
GOLDEN_CASE = "SYN-CASE-0001"
RELATED_CASE = "SYN-CASE-0002"


def login(client, username="investigator.demo"):
    response = client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200


def search_plan(intent="SEARCH"):
    return {"intent": intent, "filters": {"case_identifier": GOLDEN_FIR}, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 25, "confidence": 1, "uncertain_fields": [], "protected_tokens": [GOLDEN_FIR], "requires_confirmation": False}


def test_m6_verified_acceptance_flow(client, app):
    generate(app.extensions["repository"], app.config, "test")
    login(client)
    inv = client.post("/api/investigations", json={"title": "Verified M6 acceptance", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA", "FORENSICS_REPLICA", "VEHICLE_REPLICA"]}).json["data"]
    preview = client.post(f"/api/investigations/{inv['id']}/query/preview", json={"query": "Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi."})
    assert preview.status_code == 200
    assert client.post(f"/api/investigations/{inv['id']}/search", json=search_plan()).status_code == 200
    assert client.post(f"/api/investigations/{inv['id']}/discover", json=search_plan("DISCOVER")).status_code == 200
    case = client.get(f"/api/cases/{GOLDEN_CASE}/360").json["data"]
    source_record = case["overview"]["source_record_references"][0]
    assert client.get(f"/api/source-passports/{source_record}").status_code == 200
    for endpoint in (f"/api/m5/case-dna/{GOLDEN_CASE}/{RELATED_CASE}", f"/api/m5/graph/{GOLDEN_CASE}", f"/api/m5/assurance/{GOLDEN_CASE}", f"/api/m5/verify/{GOLDEN_CASE}/{RELATED_CASE}", f"/api/m5/actions/{GOLDEN_CASE}"):
        assert client.get(endpoint).status_code == 200
    assert client.post(f"/api/m5/challenge/{GOLDEN_CASE}", json={"hypothesis": "These cases may involve the same operational group."}).status_code == 200
    report = client.post("/api/reports", json={"title": "Verified acceptance report", "investigation_id": inv["id"], "sections": ["Cover", "Selected Sources", "Disclaimer"], "notes": "Synthetic acceptance note."}).json["data"]
    rid = report["report_id"]
    assert client.post(f"/api/reports/{rid}/assign", json={"reviewer": "supervisor.demo"}).status_code == 200
    assert client.post(f"/api/reports/{rid}/submit").status_code == 200
    client.post("/api/auth/logout"); login(client, "supervisor.demo")
    assert client.post(f"/api/reports/{rid}/review", json={"decision": "CHANGES_REQUESTED", "note": "Confirm source limitation."}).status_code == 200
    client.post("/api/auth/logout"); login(client)
    assert client.post(f"/api/reports/{rid}/versions").status_code == 200
    assert client.post(f"/api/reports/{rid}/submit").status_code == 200
    client.post("/api/auth/logout"); login(client, "supervisor.demo")
    assert client.post(f"/api/reports/{rid}/review", json={"decision": "APPROVED", "note": ""}).status_code == 200
    assert client.get(f"/api/reports/{rid}/preview").status_code == 200
    assert client.get("/api/audit-events?event_type=REPORT_SUBMITTED").status_code == 200
    assert client.get("/api/system-health").status_code == 200
