from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.audit_requests import AuditEventFilter, AuditEventInput
from backend.anvaya.services.audit import audit, list_events
from backend.anvaya.services.generator import generate


def login(client, username="investigator.demo"):
    return client.post("/api/auth/login", json={"username": username, "password": "ANVAYA-DEMO-ONLY-2026"})


def test_audit_repository_append_filter_scope_and_safe_metadata(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    investigator = repository.find_active_user_by_username("investigator.demo")
    supervisor = repository.find_active_user_by_username("supervisor.demo")
    audit(repository, "M7_AUDIT_TEST", "SUCCESS", investigator["id"], "REQ-M7", {"investigation_id": "SYN-INV-M7", "report_id": "SYN-RPT-M7", "password": "never-store", "token": "never-store"})
    audit(repository, "M7_AUDIT_TEST", "DENIED", supervisor["id"], "REQ-M7-SUP", {"report_id": "SYN-RPT-M7"})

    investigator_rows = repository.list_audit_events(AuditEventFilter(actor_user_id=investigator["id"], event_type="M7_AUDIT_TEST", limit=50))
    assert len(investigator_rows) == 1 and investigator_rows[0]["user_id"] == investigator["id"]
    metadata = json.loads(investigator_rows[0]["safe_metadata_json"])
    assert metadata == {"investigation_id": "SYN-INV-M7", "report_id": "SYN-RPT-M7"}
    combined = repository.list_audit_events(AuditEventFilter(actor_role="SUPERVISOR", report_id="SYN-RPT-M7", outcome="DENIED", request_id="REQ-M7-SUP", limit=50))
    assert len(combined) == 1 and combined[0]["user_id"] == supervisor["id"]
    assert all(isinstance(row, dict) and not hasattr(row, "execute") for row in combined)
    assert not hasattr(repository, "update_audit_event") and not hasattr(repository, "delete_audit_event")


def test_audit_filters_are_bounded_deterministic_and_reject_unsafe_shapes(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_active_user_by_username("investigator.demo")
    for index in range(3):
        audit(repository, "ORDER_TEST", "SUCCESS", user["id"], f"REQ-{index}", {"index": index})
    rows = repository.list_audit_events(AuditEventFilter(actor_user_id=user["id"], event_type="ORDER_TEST", limit=50))
    assert [(row["occurred_at"], row["id"]) for row in rows] == sorted(((row["occurred_at"], row["id"]) for row in rows), reverse=True)
    assert len(repository.list_audit_events(AuditEventFilter(actor_user_id=user["id"], event_type="ORDER_TEST", limit=1, offset=1))) == 1
    with pytest.raises(ValueError):
        AuditEventFilter(limit=51)
    with pytest.raises(ValueError):
        AuditEventFilter(offset=-1)
    with pytest.raises(TypeError):
        AuditEventFilter(order="raw SQL")
    with pytest.raises(ValueError):
        AuditEventInput("", "TYPE", "SUCCESS", None, None, "{}", "2026-01-01T00:00:00+00:00")


def test_audit_api_preserves_filters_and_investigator_supervisor_scope(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    assert login(client).status_code == 200
    investigator = repository.find_active_user_by_username("investigator.demo")
    supervisor = repository.find_active_user_by_username("supervisor.demo")
    audit(repository, "API_SCOPE", "SUCCESS", investigator["id"], "REQ-INV", {"investigation_id": "SYN-INV-M7"})
    audit(repository, "API_SCOPE", "SUCCESS", supervisor["id"], "REQ-SUP", {"report_id": "SYN-RPT-M7"})
    response = client.get("/api/audit-events", query_string={"event_type": "API_SCOPE", "limit": 999, "investigation": "SYN-INV-M7"})
    assert response.status_code == 200 and response.json["data"]["limit"] == 50
    assert all(event["user_id"] == investigator["id"] for event in response.json["data"]["events"])
    assert client.get("/api/audit-events?start=not-a-date").status_code == 400
    assert client.get("/api/audit-events?report=bad").status_code == 400
    client.post("/api/auth/logout")
    assert login(client, "supervisor.demo").status_code == 200
    response = client.get("/api/audit-events", query_string={"event_type": "API_SCOPE", "actor_role": "SUPERVISOR", "report": "SYN-RPT-M7"})
    assert response.status_code == 200 and any(event["user_id"] == supervisor["id"] for event in response.json["data"]["events"])
    assert client.delete("/api/audit-events").status_code == 405


def test_audit_placeholder_and_service_api_architecture_are_boundary_clean():
    placeholder = CatalystRepositoryPlaceholder()
    event = AuditEventInput("SYN-AUD-PLACEHOLDER", "TYPE", "SUCCESS", None, None, "{}", "2026-01-01T00:00:00+00:00")
    for operation in (lambda: placeholder.append_audit_event(event), lambda: placeholder.list_audit_events(AuditEventFilter())):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"

    root = Path(__file__).resolve().parents[1] / "anvaya"
    forbidden = ("repository.connection", ".connection.execute(", ".execute(", ".executemany(", ".commit(", ".rollback(", "import sqlite3")
    approved = {root / "services" / "generator.py"}
    for directory in (root / "services", root / "api"):
        for path in directory.rglob("*.py"):
            if path in approved:
                continue
            source = path.read_text(encoding="utf-8")
            assert not any(pattern in source for pattern in forbidden), path
