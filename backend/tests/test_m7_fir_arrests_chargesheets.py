from __future__ import annotations

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import case_360


PASSWORD = "synthetic-auth-fixture"


def _seed(app):
    repository = app.extensions["repository"]
    repository.connection.execute(
        "UPDATE users SET password_hash=? WHERE username=?",
        (generate_password_hash(PASSWORD), "investigator.demo"),
    )
    repository.connection.commit()
    generate(repository, app.config, "test")
    return repository


def _source(repository, external_id):
    source_id = f"SYN-SR-CCTNS_REPLICA-{external_id}"
    repository.connection.execute(
        "INSERT INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (source_id, "CCTNS_REPLICA", external_id, "1.0", "2026-07-12T08:00:00+00:00", "2026-07-12T08:00:00+00:00", "RESTRICTED", "Synthetic test", "Fresh", external_id, "{}"),
    )
    return source_id


def _login(client):
    return client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})


def _investigation(client):
    return client.post("/api/investigations", json={"title": "D3 FIR", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]}).get_json()["data"]


def _plan(**filters):
    return {"intent": "SEARCH", "filters": filters, "selected_sources": ["CCTNS_REPLICA"], "result_limit": 25, "confidence": 1, "uncertain_fields": [], "protected_tokens": [], "requires_confirmation": False}


def test_schema_types_fks_and_accused_link_integrity(app):
    repository = _seed(app)
    for table in ("arrest_surrender_events", "arrest_accused_links", "chargesheets"):
        assert repository.table_count(table) > 0
    invalid_event_source = _source(repository, "SYN-INVALID-EVENT")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("INSERT INTO arrest_surrender_events (id,case_id,event_type,event_at,state_code,district_code,police_unit_code,investigating_officer_ref,court_ref,remarks,source_record_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("SYN-ASE-INVALID", "SYN-CASE-0001", "DETENTION", "2026-07-12T08:00:00+00:00", None, None, None, None, None, None, invalid_event_source, "2026-07-12T08:00:00+00:00", "2026-07-12T08:00:00+00:00"))
    invalid_time_source = _source(repository, "SYN-INVALID-EVENT-TIME")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("INSERT INTO arrest_surrender_events (id,case_id,event_type,event_at,state_code,district_code,police_unit_code,investigating_officer_ref,court_ref,remarks,source_record_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("SYN-ASE-INVALID-TIME", "SYN-CASE-0001", "ARREST", "not-a-timestamp", None, None, None, None, None, None, invalid_time_source, "2026-07-12T08:00:00+00:00", "2026-07-12T08:00:00+00:00"))
    invalid_report_source = _source(repository, "SYN-INVALID-REPORT")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("INSERT INTO chargesheets (id,case_id,filed_at,report_type,filing_officer_ref,summary,source_record_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)", ("SYN-CHG-INVALID", "SYN-CASE-0001", "2026-07-12T08:00:00+00:00", "D_UNKNOWN", None, None, invalid_report_source, "2026-07-12T08:00:00+00:00", "2026-07-12T08:00:00+00:00"))
    complainant = repository.list_case_person_roles("SYN-CASE-0001", "COMPLAINANT")[0]
    link_source = _source(repository, "SYN-INVALID-NON-ACCUSED")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("INSERT INTO arrest_accused_links VALUES (?,?,?,?,?,?,?)", ("SYN-AAL-INVALID", "SYN-ASE-0001", complainant["person_id"], complainant["id"], 9, link_source, "2026-07-12T08:00:00+00:00"))
    cross_case = repository.list_case_person_roles("SYN-CASE-0002", "ACCUSED")[0]
    cross_source = _source(repository, "SYN-INVALID-CROSS-CASE")
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute("INSERT INTO arrest_accused_links VALUES (?,?,?,?,?,?,?)", ("SYN-AAL-CROSS", "SYN-ASE-0001", cross_case["person_id"], cross_case["id"], 9, cross_source, "2026-07-12T08:00:00+00:00"))


def test_repository_events_links_chargesheets_scope_and_order(app):
    repository = _seed(app)
    events = repository.list_case_arrest_surrender_events("SYN-CASE-0001", ("CCTNS_REPLICA",))
    assert events and events == sorted(events, key=lambda row: (row["event_at"], row["event_type"], row["id"]))
    assert repository.list_case_arrest_surrender_events("SYN-CASE-0024") == []
    assert repository.list_case_arrest_surrender_events("SYN-CASE-0001", ("FORENSICS_REPLICA",)) == []
    assert repository.find_arrest_surrender_event(events[0]["id"])["case_id"] == "SYN-CASE-0001"
    accused = repository.list_arrest_event_accused(events[0]["id"], ("CCTNS_REPLICA",))
    assert accused and all(row["role"] == "ACCUSED" and row["case_id"] == "SYN-CASE-0001" for row in accused)
    assert repository.list_arrest_event_accused(events[0]["id"], ("FORENSICS_REPLICA",)) == []
    chargesheets = repository.list_case_chargesheets("SYN-CASE-0001", ("CCTNS_REPLICA",))
    assert chargesheets and chargesheets == sorted(chargesheets, key=lambda row: (row["filed_at"], row["report_type"], row["id"]), reverse=True)
    assert repository.find_chargesheet(chargesheets[0]["id"])["report_type"] in {"A_CHARGESHEET", "B_FALSE", "C_UNDETECTED"}
    assert repository.list_case_chargesheets("SYN-CASE-0024") == []


def test_deterministic_fixtures_provenance_and_factual_edges(app):
    repository = _seed(app)
    assert repository.table_count("arrest_surrender_events") == 20
    assert repository.table_count("chargesheets") == 16
    assert {row["event_type"] for row in repository.list_case_arrest_surrender_events("SYN-CASE-0003")} == {"SURRENDER"}
    reports = {repository.find_chargesheet(f"SYN-CHG-{number:04d}")["report_type"] for number in range(1, 4)}
    assert reports == {"A_CHARGESHEET", "B_FALSE", "C_UNDETECTED"}
    multi = repository.list_arrest_event_accused("SYN-ASE-0001")
    assert len(multi) == 2
    edges = [dict(row) for row in repository.connection.execute("SELECT * FROM entity_edges WHERE relationship_type IN ('CASE_HAS_ARREST_EVENT','ARREST_INVOLVES_ACCUSED','CASE_HAS_CHARGESHEET')")]
    assert {row["relationship_type"] for row in edges} == {"CASE_HAS_ARREST_EVENT", "ARREST_INVOLVES_ACCUSED", "CASE_HAS_CHARGESHEET"}
    assert all(row["source_record_id"].startswith("SYN-SR-") for row in edges)


def test_case_360_timeline_masking_and_empty_sections(app):
    repository = _seed(app)
    investigator = repository.find_user_by_id("SYN-USR-INV")
    detail = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0001")
    assert detail["arrests"] and detail["chargesheets"]
    assert detail["arrests"][0]["accused"]
    assert [row["at"] for row in detail["timeline"]] == sorted(row["at"] for row in detail["timeline"])
    assert {row["kind"] for row in detail["timeline"]} >= {"ARREST", "CHARGESHEET_FILED"}
    assert all(row["source_record_id"].startswith("SYN-SR-") for row in detail["arrests"] + detail["chargesheets"])
    no_events = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0024")
    assert no_events["arrests"] == [] and no_events["chargesheets"] == []
    external = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0002")
    assert external["arrests"][0]["accused"][0]["masking"]["level"] == "EXTERNAL"


def test_api_search_filters_and_safe_contract(client, app):
    _seed(app)
    assert _login(client).status_code == 200
    investigation = _investigation(client)
    for filters in ({"arrest_event_type": "ARREST"}, {"arrest_event_type": "SURRENDER"}, {"chargesheet_report_type": "A_CHARGESHEET"}, {"has_arrest_event": True}, {"has_chargesheet": True}):
        assert client.post(f"/api/investigations/{investigation['id']}/search", json=_plan(**filters)).status_code == 200
    assert client.post(f"/api/investigations/{investigation['id']}/search", json=_plan(arrest_event_type="DETENTION")).status_code == 400
    assert client.post(f"/api/investigations/{investigation['id']}/search", json=_plan(chargesheet_report_type="D_UNKNOWN")).status_code == 400
    filters = CaseSearchFilter(arrest_event_type="ARREST", chargesheet_report_type="A_CHARGESHEET", has_arrest_event=True, has_chargesheet=True, source_system_ids=("CCTNS_REPLICA",))
    assert all(row["source_system_id"] == "CCTNS_REPLICA" for row in app.extensions["repository"].search_case_candidates(filters))
    with pytest.raises(ValueError):
        CaseSearchFilter(has_arrest_event="true", source_system_ids=("CCTNS_REPLICA",))
