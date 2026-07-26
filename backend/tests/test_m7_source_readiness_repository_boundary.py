from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.services.data_readiness import commit_import, get_import_job, validate_import
from backend.anvaya.services.source_registry import list_sources


VALID = {
    "external_id": "SYN-M7-IMPORT-001", "fir_number": "SYN-FIR-M7-001", "crime_number": "SYN-CRIME-M7-001",
    "station_id": "SYN-STN-01", "district_id": "SYN-DST-01", "offence": "CHAIN_SNATCHING",
    "incident_at": "2026-07-01T10:00:00+00:00", "registered_at": "2026-07-01T12:00:00+00:00", "status": "UNRESOLVED",
}


def test_source_registry_repository_contract_is_plain_deterministic_and_safe(app):
    repository = app.extensions["repository"]
    sources = repository.list_source_systems()
    assert [source["id"] for source in sources] == sorted(source["id"] for source in sources if source["priority"] == "P0") + ["COURT_REPLICA", "PROSECUTION_REPLICA"]
    assert all(isinstance(source, dict) and not hasattr(source, "execute") for source in sources)
    cctns = repository.find_source_system("CCTNS_REPLICA")
    assert cctns["access_class"] == "RESTRICTED"
    assert cctns["reliability_role"] == "Primary operational record"
    assert repository.find_source_system("SYN-MISSING-SOURCE") is None
    displayed = list_sources(repository)
    assert displayed[0]["status"] in {"Fresh", "Stale", "Unavailable"}
    assert {source["id"] for source in displayed if source["status"] == "Unavailable"} == {"COURT_REPLICA", "PROSECUTION_REPLICA"}


def test_import_staging_contract_preserves_failures_and_provenance(app):
    repository = app.extensions["repository"]
    result = validate_import(repository, json.dumps([VALID]).encode(), "json")
    job = repository.find_import_job(result["id"])
    assert isinstance(job, dict) and job["source_system_id"] == "CCTNS_REPLICA"
    assert repository.list_import_failures(result["id"]) == []
    assert repository.source_external_ids("CCTNS_REPLICA") == set()

    committed = commit_import(repository, result["id"])
    assert committed["status"] == "COMMITTED"
    assert VALID["external_id"] in repository.source_external_ids("CCTNS_REPLICA")
    source_record = repository.connection.execute(
        "SELECT source_system_id, external_id, version, checksum FROM source_records WHERE external_id=?",
        (VALID["external_id"],),
    ).fetchone()
    assert tuple(source_record[:3]) == ("CCTNS_REPLICA", VALID["external_id"], "synthetic-import-1.0")
    assert source_record[3]
    assert commit_import(repository, result["id"])["committed_at"] == committed["committed_at"]


def test_invalid_import_is_staged_but_not_committable(app):
    repository = app.extensions["repository"]
    bad = {"external_id": "SYN-M7-BAD"}
    result = validate_import(repository, json.dumps([bad]).encode(), "json")
    assert result["status"] == "REJECTED"
    assert result["failures"][0]["category"] == "missing_required_key"
    with pytest.raises(ApiError) as error:
        commit_import(repository, result["id"])
    assert error.value.code == "IMPORT_NOT_COMMITTABLE"
    assert get_import_job(repository, result["id"])["status"] == "REJECTED"


def test_import_commit_rolls_back_all_canonical_writes_on_late_collision(app):
    repository = app.extensions["repository"]
    second = dict(VALID, external_id="SYN-M7-IMPORT-002", fir_number="SYN-FIR-M7-002", crime_number="SYN-CRIME-M7-002")
    result = validate_import(repository, json.dumps([VALID, second]).encode(), "json")
    repository.connection.execute(
        "INSERT INTO source_records VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "SYN-M7-PREEXISTING", "CCTNS_REPLICA", second["external_id"], "synthetic-import-1.0",
            second["registered_at"], second["registered_at"], "RESTRICTED", "Primary operational record",
            "Fresh", "preexisting", "{}",
        ),
    )
    repository.connection.commit()
    cases_before = repository.table_count("cases")
    records_before = repository.table_count("source_records")

    with pytest.raises(ApiError) as error:
        commit_import(repository, result["id"])
    assert error.value.code == "IMPORT_COMMIT_FAILED"
    assert repository.table_count("cases") == cases_before
    assert repository.table_count("source_records") == records_before
    assert get_import_job(repository, result["id"])["status"] == "VALIDATED"


def test_catalyst_source_and_import_methods_fail_without_fallback():
    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.upsert_source_systems([]), lambda: placeholder.list_source_systems(),
        lambda: placeholder.find_source_system("CCTNS_REPLICA"), lambda: placeholder.source_external_ids("CCTNS_REPLICA"),
        lambda: placeholder.create_import_job({}, []), lambda: placeholder.find_import_job("SYN-IMPORT-1"),
        lambda: placeholder.list_import_failures("SYN-IMPORT-1"), lambda: placeholder.commit_import_rows("SYN-IMPORT-1", "now", []),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_source_and_data_readiness_services_have_no_sql_or_connection_access():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    source_registry = (root / "services" / "source_registry.py").read_text(encoding="utf-8")
    data_readiness = (root / "services" / "data_readiness.py").read_text(encoding="utf-8")
    api = (root / "api" / "data_readiness.py").read_text(encoding="utf-8")
    for source in (source_registry, data_readiness, api):
        assert "repository.connection" not in source
        assert ".connection.execute" not in source
        assert ".executemany(" not in source
        assert ".commit(" not in source and ".rollback(" not in source
    assert "SELECT " not in source_registry and "INSERT " not in source_registry
    assert "SELECT " not in data_readiness and "INSERT " not in data_readiness and "UPDATE " not in data_readiness
