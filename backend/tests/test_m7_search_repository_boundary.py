from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.generator import generate
from backend.anvaya.services.query_parser import parse_query
from backend.anvaya.services.search import search_cases


def test_search_repository_exact_identifier_contract_and_provenance(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    for identifier in ("SYN-CASE-0001", "SYN-FIR-000001", "SYN-CRIME-00001"):
        rows = repository.search_case_candidates(CaseSearchFilter(case_identifier=identifier, source_system_ids=("CCTNS_REPLICA",)))
        assert rows and rows[0]["id"] == "SYN-CASE-0001"
        assert isinstance(rows[0], dict) and not hasattr(rows[0], "execute")
        assert rows[0]["source_record_id"].startswith("SYN-SR-")
        assert rows[0]["source_system_id"] == "CCTNS_REPLICA"
        assert rows[0]["freshness_state"] in {"Fresh", "Stale", "Unavailable"}
        assert rows[0]["reliability_role"] and rows[0]["access_class"]
    assert repository.search_case_candidates(CaseSearchFilter(case_identifier="SYN-CASE-MISSING", source_system_ids=("CCTNS_REPLICA",))) == []


def test_structured_search_filters_are_fixed_ordered_limited_and_source_scoped(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    rows = repository.search_case_candidates(CaseSearchFilter(
        offence="CHAIN_SNATCHING", status="UNRESOLVED", location="SYN-STN-01",
        date_from="2026-03-01", date_to="2026-07-11", source_system_ids=("CCTNS_REPLICA",), limit=2,
    ))
    assert len(rows) <= 2
    assert all(row["offence"] == "CHAIN_SNATCHING" and row["status"] == "UNRESOLVED" for row in rows)
    assert [row["incident_at"] for row in rows] == sorted((row["incident_at"] for row in rows), reverse=True)
    offset_rows = repository.search_case_candidates(CaseSearchFilter(source_system_ids=("CCTNS_REPLICA",), limit=1, offset=1))
    assert len(offset_rows) == 1
    assert repository.search_case_candidates(CaseSearchFilter(source_system_ids=("VEHICLE_REPLICA",))) == []


def test_search_filter_rejects_unbounded_or_unsupported_inputs():
    with pytest.raises(ValueError, match="limit"):
        CaseSearchFilter(limit=26)
    with pytest.raises(ValueError, match="offset"):
        CaseSearchFilter(offset=-1)
    with pytest.raises(ValueError, match="unique"):
        CaseSearchFilter(source_system_ids=("CCTNS_REPLICA", "CCTNS_REPLICA"))
    with pytest.raises(TypeError):
        CaseSearchFilter(order="raw SQL")
    with pytest.raises(TypeError):
        CaseSearchFilter(sql="SELECT * FROM cases")


def test_search_service_preserves_policy_masking_and_kannada_english_normalisation(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    plan = parse_query("Find SYN-FIR-000002", ["CCTNS_REPLICA"])
    results = search_cases(repository, user, "Active Case Investigation", plan)
    assert results and results[0]["masking"]["level"] == "EXTERNAL"
    golden = parse_query(
        "Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.",
        ["CCTNS_REPLICA"],
    )
    assert golden.filters.location == "JAYANAGAR"
    assert golden.filters.status == "UNRESOLVED"
    assert golden.filters.offence == "CHAIN_SNATCHING"


def test_catalyst_search_placeholder_fails_without_fallback():
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().search_case_candidates(CaseSearchFilter())
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_search_service_has_no_direct_sql_or_connection_access():
    source = (Path(__file__).resolve().parents[1] / "anvaya" / "services" / "search.py").read_text(encoding="utf-8")
    assert "repository.connection" not in source
    assert ".execute(" not in source and ".executemany(" not in source
    assert "SELECT " not in source and "INSERT " not in source and "UPDATE " not in source
