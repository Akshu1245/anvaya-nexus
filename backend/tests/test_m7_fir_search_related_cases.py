"""D-7 FIR search summaries and transparent related-case reasons."""

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.repositories.audit_requests import AuditEventFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import related_cases
from backend.anvaya.services.search import search_cases
from backend.anvaya.schemas.query import QueryPlan


def _plan(**filters):
    return QueryPlan.model_validate({"intent": "SEARCH", "filters": filters, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 25, "confidence": 1})


def test_fir_search_requires_filter_and_returns_dataset_summary(app):
    repository = app.extensions["repository"]; generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    with pytest.raises(ApiError) as error:
        search_cases(repository, user, "Active Case Investigation", _plan())
    assert error.value.code == "SEARCH_FILTER_REQUIRED"
    case = repository.find_case_360_case("SYN-CASE-0001")
    rows = search_cases(repository, user, "Active Case Investigation", _plan(crime_number=case["crime_number"]))
    assert len(rows) == 1
    result = rows[0]
    assert {"case_id", "crime_number", "case_number", "registered_at", "canonical_status", "police_unit", "acts_sections", "has_arrest_surrender", "has_chargesheet", "freshness_state"} <= set(result)
    assert "payload_json" not in result and "original_source_value" not in result
    with pytest.raises(ValueError):
        CaseSearchFilter(date_from="2026-02-02", date_to="2026-02-01", source_system_ids=("CCTNS_REPLICA",))


def test_related_cases_are_factual_ordered_and_score_free(app):
    repository = app.extensions["repository"]; generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    result = related_cases(repository, user, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",), 10)
    assert result["base_case"]["case_id"] == "SYN-CASE-0001"
    assert result["related_cases"]
    allowed = {"SHARED_ACCUSED", "SHARED_ARREST_ACCUSED", "SHARED_COMPLAINANT", "SHARED_VICTIM", "SHARED_ACT_SECTION", "SHARED_POLICE_UNIT", "SHARED_COURT", "SHARED_REGISTERING_OFFICER", "SHARED_CRIME_MINOR_HEAD", "SHARED_CRIME_MAJOR_HEAD", "SHARED_CASE_CATEGORY", "SHARED_GRAVITY", "SHARED_CANONICAL_STATUS", "TEMPORAL_OVERLAP"}
    for row in result["related_cases"]:
        assert row["case_id"] != "SYN-CASE-0001"
        assert row["related_reasons"]
        assert {reason["reason_type"] for reason in row["related_reasons"]} <= allowed
        assert all(reason["confidence_class"] in {"DIRECT_SHARED_RECORD", "SHARED_CLASSIFICATION", "TEMPORAL_OVERLAP"} for reason in row["related_reasons"])
        assert "score" not in row and "probability" not in row
    assert "does not imply guilt" in result["metadata"]["limitations"]
    assert [row["case_id"] for row in result["related_cases"]] == [row["case_id"] for row in related_cases(repository, user, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",), 10)["related_cases"]]


def test_related_case_api_audits_and_respects_investigation_scope(client, app):
    repository = app.extensions["repository"]; generate(repository, app.config, "test")
    login = client.post("/api/auth/login", json={"username": "investigator.demo", "password": client.application.config["DEMO_PASSWORD"]})
    assert login.status_code == 200
    created = client.post("/api/investigations", json={"title": "FIR related", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).get_json()["data"]
    response = client.get(f"/api/investigations/{created['id']}/cases/SYN-CASE-0001/related")
    assert response.status_code == 200
    assert "related_cases" in response.get_json()["data"]
    assert any(event["event_type"] == "RELATED_CASES_VIEWED" for event in repository.list_audit_events(AuditEventFilter(actor_user_id="SYN-USR-INV", limit=25)))
