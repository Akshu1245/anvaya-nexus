from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.services.generator import generate


PASSWORD = "ANVAYA-DEMO-ONLY-2026"


def login(client, username="investigator.demo"):
    response = client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200


def create_report(client):
    investigation = client.post("/api/investigations", json={"title": "M7 report boundary", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).json["data"]
    response = client.post("/api/reports", json={"title": "Boundary report", "investigation_id": investigation["id"], "sections": ["Cover", "Reviewer Notes", "Disclaimer"], "notes": "Synthetic note."})
    assert response.status_code == 201
    return response.json["data"]["report_id"]


def test_report_repository_fixed_records_lists_versions_and_preview_inputs(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    login(client)
    report_id = create_report(client)

    report = repository.find_report(report_id)
    assert isinstance(report, dict) and report["status"] == "DRAFT"
    assert repository.find_report("SYN-RPT-MISSING") is None
    owned = repository.list_reports_owned_by(report["owner_user_id"], 500, 0)
    assert any(row["id"] == report_id for row in owned) and len(owned) <= 50
    assert all(isinstance(row, dict) and not hasattr(row, "execute") for row in owned)
    current = repository.find_current_report_version(report_id)
    assert current and current["version_number"] == 1 and json.loads(current["sections_json"])
    assert repository.find_report_version(report_id, 99) is None
    assert [row["version_number"] for row in repository.list_report_versions(report_id)] == [1]


def test_report_lifecycle_repository_preserves_assignment_immutability_and_append_only_history(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    login(client)
    report_id = create_report(client)
    original = repository.find_report(report_id)
    assert client.post(f"/api/reports/{report_id}/assign", json={"reviewer": "analyst.demo"}).status_code == 400
    assert repository.find_report(report_id)["assigned_reviewer_id"] == original["assigned_reviewer_id"]
    assert client.post(f"/api/reports/{report_id}/assign", json={"reviewer": "supervisor.demo"}).status_code == 200
    assert client.post(f"/api/reports/{report_id}/submit").status_code == 200
    submitted = repository.find_report_version(report_id, 1)
    assert submitted["immutable"] == 1 and submitted["status"] == "IN_REVIEW"
    with pytest.raises(ApiError) as error:
        repository.update_report_draft(report_id, 1, "tamper", "[]", "tamper", "tamper", "2030-01-01T00:00:00+00:00")
    assert error.value.code == "REPORT_IMMUTABLE"
    assert repository.find_report_version(report_id, 1)["notes"] == submitted["notes"]

    client.post("/api/auth/logout")
    login(client, "supervisor.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "CHANGES_REQUESTED", "note": "Need confirmation."}).status_code == 200
    history = repository.list_report_review_history(report_id)
    assert history and history[0]["decision"] == "CHANGES_REQUESTED" and history[0]["version_number"] == 1
    client.post("/api/auth/logout")
    login(client)
    assert client.post(f"/api/reports/{report_id}/versions").status_code == 200
    assert repository.find_current_report_version(report_id)["version_number"] == 2
    assert repository.find_report_version(report_id, 1)["immutable"] == 1
    assert client.post(f"/api/reports/{report_id}/submit").status_code == 200
    client.post("/api/auth/logout")
    login(client, "supervisor.demo")
    assert client.post(f"/api/reports/{report_id}/review", json={"decision": "APPROVED", "note": ""}).status_code == 200
    assert repository.find_report(report_id)["status"] == "APPROVED"
    assert [row["version_number"] for row in repository.list_report_versions(report_id)] == [2, 1]


def test_report_scope_queue_preview_and_catalyst_placeholder_are_safe(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    login(client)
    report_id = create_report(client)
    assert client.post(f"/api/reports/{report_id}/assign", json={"reviewer": "supervisor.demo"}).status_code == 200
    assert client.post(f"/api/reports/{report_id}/submit").status_code == 200
    client.post("/api/auth/logout")
    login(client, "supervisor.demo")
    queue = repository.list_reports_assigned_to(repository.find_active_user_by_username("supervisor.demo")["id"], 25, 0)
    assert any(row["id"] == report_id for row in queue)
    assert client.get(f"/api/reports/{report_id}/preview-metadata").json["data"]["native_pdf_available"] is False
    assert client.get(f"/api/reports/{report_id}/preview-metadata").json["data"]["browser_print_to_pdf_available"] is True
    assert client.get(f"/api/reports/{report_id}/preview").status_code == 200

    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.find_report(report_id),
        lambda: placeholder.list_reports_owned_by("SYN-USR-INV", 1, 0),
        lambda: placeholder.find_eligible_supervisor("supervisor.demo"),
        lambda: placeholder.find_current_report_version(report_id),
        lambda: placeholder.list_report_review_history(report_id),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_report_service_and_report_api_handlers_are_sql_free():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    service = (root / "services" / "reports.py").read_text(encoding="utf-8")
    assert "repository.connection" not in service and "repo.connection" not in service
    assert ".execute(" not in service and ".executemany(" not in service
    assert "SELECT " not in service and "INSERT " not in service and "UPDATE " not in service

    api = (root / "api" / "m3.py").read_text(encoding="utf-8")
    for name in ("reports_create", "reports_list", "reports_detail", "reports_version", "reviewers", "reports_assign", "reports_submit", "reports_update", "reports_new_version", "reports_preview", "reports_preview_metadata", "reports_review"):
        handler = api.split(f"def {name}", 1)[1].split("\n@", 1)[0]
        assert "connection" not in handler and ".execute(" not in handler and ".executemany(" not in handler
    assert "generic_report_query" not in (root / "repositories" / "base.py").read_text(encoding="utf-8")
