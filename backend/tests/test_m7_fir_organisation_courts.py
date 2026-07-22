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


def test_organisation_schema_catalogues_and_hierarchy_constraints(app):
    repository = _seed(app)
    assert repository.schema_version() == 16
    assert repository.table_count("states") == 2
    assert repository.table_count("districts") == 4
    assert repository.table_count("police_units") == 8
    assert repository.table_count("police_employees") == 12
    assert repository.table_count("courts") == 5
    with pytest.raises(sqlite3.IntegrityError):
        repository.connection.execute(
            "UPDATE cases SET state_id=?,canonical_district_id=? WHERE id=?",
            ("SYN-STATE-01", "SYN-DIST-04", "SYN-CASE-0001"),
        )


def test_repository_catalogues_ordering_and_case_organisation(app):
    repository = _seed(app)
    assert [row["code"] for row in repository.list_districts("SYN-STATE-01")] == ["D01", "D02", "D03"]
    assert len(repository.list_police_units()) == 7
    assert len(repository.list_police_employees()) == 11
    assert len(repository.list_courts()) == 4
    assert repository.find_state("SYN-STATE-01")["name"] == "Synthetic State One"
    organisation = repository.find_case_organisation("SYN-CASE-0001")
    assert organisation["unit_code"] and organisation["officer_name"] and organisation["court_code"]
    assert repository.find_case_organisation("missing") is None
    with pytest.raises(ValueError):
        repository.list_states("yes")


def test_case_360_search_and_factual_graph_support(app):
    repository = _seed(app)
    user = repository.find_user_by_id("SYN-USR-INV")
    detail = case_360(repository, user, "Active Case Investigation", "SYN-CASE-0001")
    assert detail["organisation"]["unit_name"]
    assert detail["arrests"][0]["organisation"]["police_unit"]
    assert detail["chargesheets"][0]["filing_officer"]
    filters = CaseSearchFilter(state="SYN-KA", district="D01", police_unit="U01", registering_officer="SYN-EMP-001", court="C01", source_system_ids=("CCTNS_REPLICA",))
    rows = repository.search_case_candidates(filters)
    assert rows and all(row["source_system_id"] == "CCTNS_REPLICA" for row in rows)
    edge_types = {row["relationship_type"] for row in repository.connection.execute("SELECT relationship_type FROM entity_edges")}
    assert {"CASE_REGISTERED_AT_UNIT", "CASE_REGISTERED_BY_OFFICER", "CASE_HEARD_AT_COURT", "OFFICER_ASSIGNED_TO_UNIT", "UNIT_BELONGS_TO_DISTRICT", "DISTRICT_BELONGS_TO_STATE"} <= edge_types
