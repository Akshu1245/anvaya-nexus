from __future__ import annotations

import sqlite3

import pytest

from backend.anvaya.repositories.person_roles import CASE_PERSON_ROLES
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import case_360


PASSWORD = "ANVAYA-DEMO-ONLY-2026"


def _seed(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    return repository


def _login(client, username="investigator.demo"):
    return client.post("/api/auth/login", json={"username": username, "password": PASSWORD})


def _investigation(client):
    response = client.post(
        "/api/investigations",
        json={"title": "FIR people", "purpose": "Active Case Investigation", "selected_sources": ["CCTNS_REPLICA"]},
    )
    return response.get_json()["data"]


def _plan(name, role):
    return {
        "intent": "SEARCH",
        "filters": {"person_name": name, "person_role": role},
        "selected_sources": ["CCTNS_REPLICA"],
        "result_limit": 25,
        "confidence": 1,
        "uncertain_fields": [],
        "protected_tokens": [],
        "requires_confirmation": False,
    }


def test_people_role_schema_constraints_and_safe_columns(app):
    repository = _seed(app)
    columns = {row[1] for row in repository.connection.execute("PRAGMA table_info(case_person_roles)")}
    assert {"id", "case_id", "person_id", "role", "role_sequence", "source_record_id", "created_at"} <= columns
    person_columns = {row[1] for row in repository.connection.execute("PRAGMA table_info(persons)")}
    assert {"id", "display_name", "age_years", "gender_code", "source_record_id", "created_at", "updated_at"} <= person_columns
    assert not {"caste", "religion", "blood_group", "disability", "date_of_birth"} & person_columns
    role = repository.list_case_person_roles("SYN-CASE-0001", "ACCUSED")[0]
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "INSERT INTO case_person_roles VALUES (?,?,?,?,?,?,?)",
            ("SYN-CPR-INVALID", role["case_id"], role["person_id"], "INFORMANT", None, "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001", role["created_at"]),
        )
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "INSERT INTO case_person_roles VALUES (?,?,?,?,?,?,?)",
            ("SYN-CPR-SEQUENCE", role["case_id"], role["person_id"], "ACCUSED", 0, "SYN-SR-CCTNS_REPLICA-SYN-CASE-0002", role["created_at"]),
        )
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "INSERT INTO case_person_roles VALUES (?,?,?,?,?,?,?)",
            ("SYN-CPR-ORPHAN", "SYN-CASE-MISSING", role["person_id"], "ACCUSED", 9, "SYN-SR-CCTNS_REPLICA-SYN-CASE-0003", role["created_at"]),
        )


def test_repository_lists_roles_with_scope_order_and_name_search(app):
    repository = _seed(app)
    rows = repository.list_case_people("SYN-CASE-0001", ("CCTNS_REPLICA",))
    assert [row["role"] for row in rows] == ["ACCUSED", "ACCUSED", "COMPLAINANT", "VICTIM", "WITNESS"]
    assert [row["role_sequence"] for row in rows[:2]] == [1, 2]
    assert repository.list_case_person_roles("SYN-CASE-0001", "VICTIM")[0]["role"] == "VICTIM"
    assert repository.list_case_person_roles("SYN-CASE-0001", "WITNESS")[0]["role"] == "WITNESS"
    assert repository.list_case_person_roles("SYN-CASE-MISSING") == []
    assert repository.list_case_people("SYN-CASE-0001", ("FORENSICS_REPLICA",)) == []
    with pytest.raises(ValueError):
        repository.list_case_person_roles("SYN-CASE-0001", "INFORMANT")
    matches = repository.search_case_people_name("Synthetic Person 0001", "ACCUSED", ("CCTNS_REPLICA",), 2)
    assert [row["id"] for row in matches] == ["SYN-CASE-0001", "SYN-CASE-0002"]
    assert repository.search_case_people_name("Synthetic Person 0001", "ACCUSED", ("FORENSICS_REPLICA",), 25) == []
    assert repository.find_person("SYN-PER-0001")["id"] == "SYN-PER-0001"
    assert repository.find_person("SYN-PER-MISSING") is None


def test_generator_maps_official_roles_with_provenance_and_factual_edges(app):
    repository = _seed(app)
    assert set(CASE_PERSON_ROLES) == {"COMPLAINANT", "VICTIM", "ACCUSED", "WITNESS"}
    repeated = repository.list_case_person_roles("SYN-CASE-0001", "ACCUSED")[0]["person_id"]
    assert repeated == "SYN-PER-0001"
    assert repeated in {row["person_id"] for row in repository.list_case_person_roles("SYN-CASE-0002", "ACCUSED")}
    assert repository.list_case_person_roles("SYN-CASE-0003", "VICTIM") == []
    roles = repository.list_case_people("SYN-CASE-0001")
    assert all(row["source_record_id"].startswith("SYN-SR-") for row in roles)
    edges = [dict(row) for row in repository.connection.execute(
        "SELECT * FROM entity_edges WHERE source_id='SYN-CASE-0001' AND relationship_type IN ('CASE_HAS_COMPLAINANT','CASE_HAS_VICTIM','CASE_HAS_ACCUSED') ORDER BY id"
    )]
    assert {edge["relationship_type"] for edge in edges} == {"CASE_HAS_COMPLAINANT", "CASE_HAS_VICTIM", "CASE_HAS_ACCUSED"}
    assert all(edge["source_record_id"].startswith("SYN-SR-") and edge["target_type"] == "PERSON" for edge in edges)


def test_case_360_groups_people_inside_privacy_safe_primary_sections(app):
    repository = _seed(app)
    investigator = repository.find_user_by_id("SYN-USR-INV")
    external = case_360(repository, investigator, "Active Case Investigation", "SYN-CASE-0002")

    assert {
        "sections",
        "case",
        "incident",
        "people",
        "legal_provisions",
        "classification",
        "police_and_court",
        "arrest_section",
        "chargesheet_section",
        "evidence_section",
        "data_quality",
        "assurance",
        "sources",
        "timeline",
    } <= external.keys()
    assert not {"complainants", "victims", "accused", "entities"} & external.keys()

    people = external["people"]
    assert people["complainants"] and people["accused"]
    assert all(row["role"] == "ACCUSED" for row in people["accused"])
    assert people["accused"][0]["role_sequence"] == 1
    assert all(row["masking"]["level"] == "EXTERNAL" for row in people["complainants"] + people["accused"])
    assert all(
        "birth_year" not in row and "address" not in row and "payload_json" not in row
        for section in ("complainants", "victims", "accused")
        for row in people[section]
    )


def test_api_person_role_search_and_case_360_sections(client, app):
    _seed(app)
    assert _login(client).status_code == 200
    investigation = _investigation(client)
    for role in CASE_PERSON_ROLES:
        response = client.post(f"/api/investigations/{investigation['id']}/search", json=_plan("Synthetic Person 0001", role))
        assert response.status_code == 200
    invalid = _plan("Synthetic Person 0001", "INFORMANT")
    assert client.post(f"/api/investigations/{investigation['id']}/search", json=invalid).status_code == 400
    result = client.get("/api/cases/SYN-CASE-0001/360?purpose=Active%20Case%20Investigation")
    assert result.status_code == 200
    body = result.get_json()["data"]
    assert body["people"]["complainants"] and body["people"]["victims"] and len(body["people"]["accused"]) == 2


def test_person_search_filter_has_bounded_allowlisted_contract():
    assert CaseSearchFilter(person_name="Synthetic Person", person_role="COMPLAINANT", source_system_ids=("CCTNS_REPLICA",)).person_role == "COMPLAINANT"
    with pytest.raises(ValueError):
        CaseSearchFilter(person_name="%", source_system_ids=("CCTNS_REPLICA",))
    assert CaseSearchFilter(person_role="WITNESS", source_system_ids=("CCTNS_REPLICA",)).person_role == "WITNESS"
    with pytest.raises(ValueError):
        CaseSearchFilter(person_role="INFORMANT", source_system_ids=("CCTNS_REPLICA",))
