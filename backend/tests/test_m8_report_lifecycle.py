import json
import sqlite3

import pytest

from backend.anvaya.services.generator import generate


def _login(client, app, username="investigator.demo"):
    return client.post("/api/auth/login", json={"username": username, "password": app.config["DEMO_PASSWORD"]})


def _report(client):
    investigation = client.post("/api/investigations", json={
        "title": "Synthetic report lifecycle", "purpose": "Active Case Investigation",
        "selected_sources": ["CCTNS_REPLICA"],
    }).get_json()["data"]
    return client.post("/api/reports", json={
        "title": "Synthetic grounded report", "investigation_id": investigation["id"],
        "sections": ["Cover", "Selected Sources", "Sources and Provenance", "Reviewer Notes", "Disclaimer"],
        "notes": "Synthetic source-backed note.",
    }).get_json()["data"]


def _assign_submit(client, report_id):
    assert client.post(f"/api/reports/{report_id}/assign", json={"reviewer": "supervisor.demo"}).status_code == 200
    assert client.post(f"/api/reports/{report_id}/submit").status_code == 200


def test_draft_grounding_warning_disclaimer_safe_update_and_submit_immutability(client, app):
    generate(app.extensions["repository"], app.config, "test")
    _login(client, app)
    created = _report(client)
    report_id = created["report_id"]
    document = created["html"]
    assert "Human review required" in document
    assert "SYNTHETIC DATATHON PROTOTYPE" in document
    assert "CCTNS_REPLICA" in document
    assert client.patch(f"/api/reports/{report_id}", json={
        "title": "Updated synthetic report", "sections": ["Cover", "Reviewer Notes", "Disclaimer"],
        "notes": "Updated synthetic note.",
    }).status_code == 200
    assert client.patch(f"/api/reports/{report_id}", json={
        "title": "<script>alert(1)</script>", "sections": ["Cover"], "notes": "safe",
    }).status_code == 400
    assert client.patch(f"/api/reports/{report_id}", json={
        "title": "Safe", "sections": ["Reviewer Notes"], "notes": "<img src=x onerror=alert(1)>",
    }).status_code == 400
    _assign_submit(client, report_id)
    assert client.patch(f"/api/reports/{report_id}", json={
        "title": "Rewrite attempt", "sections": ["Cover"], "notes": "Synthetic",
    }).status_code == 409
    version = client.get(f"/api/reports/{report_id}/versions/1").get_json()["data"]
    assert version["immutable"] == 1 and version["created_by"] == "SYN-USR-INV"


def test_return_requires_reason_and_new_version_preserves_author_reviewer_history(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    _login(client, app)
    report_id = _report(client)["report_id"]
    _assign_submit(client, report_id)
    client.post("/api/auth/logout"); _login(client, app, "supervisor.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "CHANGES_REQUESTED", "note": ""}).status_code == 400
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "CHANGES_REQUESTED", "note": "Verify cited synthetic source."}).status_code == 200
    client.post("/api/auth/logout"); _login(client, app)
    assert client.post(f"/api/reports/{report_id}/submit").status_code == 409
    created = client.post(f"/api/reports/{report_id}/versions")
    assert created.status_code == 200 and created.get_json()["data"]["version_id"].endswith("-V2")
    assert client.patch(f"/api/reports/{report_id}", json={
        "title": "Synthetic revised report", "sections": ["Cover", "Disclaimer"], "notes": "Revised synthetic note.",
    }).status_code == 200
    detail = client.get(f"/api/reports/{report_id}").get_json()["data"]
    versions = {item["version_number"]: item for item in detail["versions"]}
    assert versions[1]["immutable"] == 1 and versions[2]["immutable"] == 0
    assert versions[1]["created_by"] == versions[2]["created_by"] == "SYN-USR-INV"
    assert detail["review_history"] == [{
        "decision": "CHANGES_REQUESTED", "note": "Verify cited synthetic source.",
        "created_at": detail["review_history"][0]["created_at"], "username": "supervisor.demo", "version_number": 1,
    }]


def test_approval_scope_audit_events_and_append_only_storage(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    _login(client, app)
    report_id = _report(client)["report_id"]
    assert client.patch(f"/api/reports/{report_id}", json={"title": "Synthetic update", "sections": ["Cover", "Disclaimer"], "notes": "Synthetic."}).status_code == 200
    _assign_submit(client, report_id)
    assert client.get(f"/api/reports/{report_id}").status_code == 200
    assert client.get(f"/api/reports/{report_id}/versions/1").status_code == 200
    client.post("/api/auth/logout"); _login(client, app, "analyst.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "APPROVED", "note": ""}).status_code == 403
    client.post("/api/auth/logout"); _login(client, app, "supervisor.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "APPROVED", "note": ""}).status_code == 200
    detail = client.get(f"/api/reports/{report_id}").get_json()["data"]
    assert detail["report"]["owner_user_id"] == "SYN-USR-INV"
    assert detail["report"]["assigned_reviewer_id"] == "SYN-USR-SUP"
    assert detail["review_history"][0]["username"] == "supervisor.demo"

    events = {row[0] for row in repository.connection.execute("SELECT event_type FROM audit_events")}
    assert {
        "REPORT_DRAFT_CREATED", "REPORT_DRAFT_UPDATED", "REPORT_SUBMITTED", "REPORT_VIEWED",
        "REPORT_VERSION_VIEWED", "REPORT_REVIEWED", "REPORT_APPROVED", "PERMISSION_DENIAL",
    } <= events
    audit_id = repository.connection.execute("SELECT id FROM audit_events LIMIT 1").fetchone()[0]
    review_id = repository.connection.execute("SELECT id FROM report_reviews LIMIT 1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("UPDATE audit_events SET outcome='ALTERED' WHERE id=?", (audit_id,))
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("DELETE FROM report_reviews WHERE id=?", (review_id,))
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("UPDATE report_versions SET notes='rewrite' WHERE report_id=? AND version_number=1", (report_id,))


def test_return_and_new_version_have_distinct_audit_events(client, app):
    generate(app.extensions["repository"], app.config, "test")
    _login(client, app)
    report_id = _report(client)["report_id"]
    _assign_submit(client, report_id)
    client.post("/api/auth/logout"); _login(client, app, "supervisor.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "CHANGES_REQUESTED", "note": "Return reason"}).status_code == 200
    client.post("/api/auth/logout"); _login(client, app)
    assert client.post(f"/api/reports/{report_id}/versions").status_code == 200
    events = {row[0] for row in app.extensions["repository"].connection.execute("SELECT event_type FROM audit_events")}
    assert {"REPORT_RETURNED", "REPORT_VERSION_CREATED"} <= events
