from __future__ import annotations

import sqlite3

import pytest

from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import case_360


def _seed(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    return repository


def _login(client):
    return client.post("/api/auth/login", json={"username": "investigator.demo", "password": client.application.config["DEMO_PASSWORD"]})


def _investigation(client):
    return client.post("/api/investigations", json={"title": "FIR legal", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).get_json()["data"]


def _plan(**filters):
    return {"intent": "SEARCH", "filters": filters, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 25, "confidence": 1, "uncertain_fields": [], "protected_tokens": [], "requires_confirmation": False}


def _fresh_source(repository, external_id):
    repository.connection.execute(
        "INSERT INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (f"SYN-SR-CCTNS_REPLICA-{external_id}", "CCTNS_REPLICA", external_id, "1.0", "2026-07-11T08:00:00+00:00", "2026-07-11T08:00:00+00:00", "RESTRICTED", "Synthetic test", "Fresh", external_id, "{}"),
    )
    return f"SYN-SR-CCTNS_REPLICA-{external_id}"


def test_legal_schema_constraints_and_case_references(app):
    repository = _seed(app)
    for table in ("legal_acts", "legal_sections", "case_legal_sections", "case_categories", "gravity_offences", "crime_heads", "crime_subheads", "case_statuses"):
        assert repository.table_count(table) > 0
    case_columns = {row[1] for row in repository.connection.execute("PRAGMA table_info(cases)")}
    assert {"case_category_id", "gravity_offence_id", "crime_major_head_id", "crime_minor_head_id", "case_status_id"} <= case_columns
    source = _fresh_source(repository, "SYN-TEST-LEGAL-MISMATCH")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "INSERT INTO case_legal_sections VALUES (?,?,?,?,?,?,?,?)",
            ("SYN-CLS-MISMATCH", "SYN-CASE-0001", "SYN-ACT-01", "SYN-SEC-02-01", 1, 1, source, "2026-07-11T08:00:00+00:00"),
        )
    source = _fresh_source(repository, "SYN-TEST-LEGAL-ORDER")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "INSERT INTO case_legal_sections VALUES (?,?,?,?,?,?,?,?)",
            ("SYN-CLS-ZERO", "SYN-CASE-0001", "SYN-ACT-01", "SYN-SEC-01-02", 0, 1, source, "2026-07-11T08:00:00+00:00"),
        )


def test_repository_legal_lists_classifications_scope_and_order(app):
    repository = _seed(app)
    assert len(repository.list_legal_acts()) == 5
    assert len(repository.list_legal_acts(False)) == 6
    assert [row["section_code"] for row in repository.list_legal_sections("SYN-ACT-01")] == ["S-01-01", "S-01-02", "S-01-03"]
    assert [row["section_code"] for row in repository.list_legal_sections("SYN-ACT-01", False)] == ["S-01-01", "S-01-02", "S-01-03", "S-01-04"]
    assert repository.find_legal_act("SYN-ACT-01")["act_code"] == "SYN-ACT-01"
    assert repository.find_legal_section("SYN-SEC-01-01")["act_id"] == "SYN-ACT-01"
    assert repository.find_legal_act("SYN-ACT-MISSING") is None
    links = repository.list_case_legal_sections("SYN-CASE-0001", ("CCTNS_REPLICA",))
    assert [(row["act_order"], row["section_order"], row["act_code"], row["section_code"]) for row in links] == sorted((row["act_order"], row["section_order"], row["act_code"], row["section_code"]) for row in links)
    assert repository.list_case_legal_sections("SYN-CASE-0001", ("FORENSICS_REPLICA",)) == []
    classifications = repository.find_case_classifications("SYN-CASE-0001")
    assert classifications["category"]["code"] == "PROPERTY" and classifications["canonical_status"]["code"] == "UNRESOLVED"
    assert repository.find_case_classifications("SYN-CASE-MISSING") is None
    assert repository.find_case_classifications("SYN-CASE-0009")["category"]["active"] == 0
    with pytest.raises(ValueError):
        repository.list_case_categories("yes")


def test_generator_provenance_repeated_sections_inactive_scenarios_and_edges(app):
    repository = _seed(app)
    assert repository.table_count("legal_acts") == 6
    assert repository.table_count("legal_sections") == 24
    assert repository.table_count("case_legal_sections") == 32
    assert all(row["source_record_id"].startswith("SYN-SR-") for row in repository.list_case_legal_sections("SYN-CASE-0001"))
    shared = {row["section_id"] for row in repository.list_case_legal_sections("SYN-CASE-0001")} & {row["section_id"] for row in repository.list_case_legal_sections("SYN-CASE-0002")}
    assert "SYN-SEC-02-01" in shared
    inactive = repository.list_case_legal_sections("SYN-CASE-0007")[0]
    assert inactive["section_active"] == 0
    edges = [dict(row) for row in repository.connection.execute("SELECT * FROM entity_edges WHERE source_id='SYN-CASE-0001' AND relationship_type IN ('CASE_INVOKES_ACT','CASE_INVOKES_SECTION') ORDER BY id")]
    assert {row["relationship_type"] for row in edges} == {"CASE_INVOKES_ACT", "CASE_INVOKES_SECTION"}
    assert all(row["source_record_id"].startswith("SYN-SR-") for row in edges)


def test_case_360_legal_classifications_and_masking_are_additive(app):
    repository = _seed(app)
    investigator = repository.find_user_by_id("SYN-USR-INV")
    result = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0002")
    assert result["legal"] and result["classifications"]
    assert result["overview"]["offence"] and result["overview"]["status"]
    assert all({"act_code", "section_code", "act_active", "section_active", "source_record_id"} <= row.keys() for row in result["legal"])
    inactive = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0007")
    assert inactive["legal"][0]["section_active"] == 0
    assert case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0003")["legal"]


def test_api_structured_fir_legal_and_classification_search(client, app):
    _seed(app)
    assert _login(client).status_code == 200
    investigation = _investigation(client)
    for filters in ({"act_code": "SYN-ACT-01"}, {"section_code": "S-02-01"}, {"case_category": "PROPERTY"}, {"gravity_offence": "HIGH"}, {"crime_major_head": "SYN-HEAD-PROPERTY"}, {"crime_minor_head": "SYN-SUB-01-01"}, {"canonical_case_status": "UNRESOLVED"}):
        response = client.post(f"/api/investigations/{investigation['id']}/search", json=_plan(**filters))
        assert response.status_code == 200
    bad = _plan(act_code="illegal text")
    assert client.post(f"/api/investigations/{investigation['id']}/search", json=bad).status_code == 400
    detail = client.get("/api/cases/SYN-CASE-0001/360?purpose=Active%20Case%20Investigation").get_json()["data"]
    assert "legal" in detail and "classifications" in detail


def test_legal_search_filter_is_bounded_and_no_protected_or_recommendation_fields(app):
    repository = _seed(app)
    filters = CaseSearchFilter(act_code="SYN-ACT-01", section_code="S-01-01", source_system_ids=("CCTNS_REPLICA",))
    matches = repository.search_case_candidates(filters)
    assert "SYN-CASE-0001" in {row["id"] for row in matches}
    assert all(row["source_system_id"] == "CCTNS_REPLICA" for row in matches)
    with pytest.raises(ValueError):
        CaseSearchFilter(act_code="x" * 65, source_system_ids=("CCTNS_REPLICA",))
    result = case_360(repository, repository.find_user_by_id("SYN-USR-INV"), "Active Case Investigation", "SYN-CASE-0001")
    serialised = str(result).lower()
    for token in ("caste", "religion", "blood_group", "disability", "recommendation", "punishment"):
        assert token not in serialised
