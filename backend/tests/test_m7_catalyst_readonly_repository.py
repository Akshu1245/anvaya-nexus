"""Contract checks for the offline-only fake-backed Catalyst read slice."""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.services.generator import generate
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient


def _user(**overrides):
    record = {
        "ROWID": "row-user", "id": "SYN-USR-INV", "username": "investigator.demo",
        "password_hash": "safe-prototype-hash", "role": "INVESTIGATOR",
        "assigned_station": None, "assigned_district": None, "active": "true",
    }
    record.update(overrides)
    return record


def _source(**overrides):
    record = {
        "ROWID": "row-source", "id": "CCTNS_REPLICA", "name": "CCTNS Replica",
        "source_tier": "PRIMARY", "access_class": "RESTRICTED",
        "reliability_role": "Primary operational record", "status": "Fresh",
        "last_successful_sync": None, "freshness_threshold_hours": "24", "version": "1.0",
        "connector_type": "SYNTHETIC", "description": "Synthetic source", "priority": "P0",
    }
    record.update(overrides)
    return record


def _case(**overrides):
    record = {
        "ROWID": "row-case", "id": "SYN-CASE-0001", "fir_number": "SYN-FIR-000001",
        "crime_number": "SYN-CRIME-00001", "station_id": "SYN-STN-01", "district_id": "SYN-DST-01",
        "offence": "CHAIN_SNATCHING", "incident_at": "2026-07-01T08:00:00+00:00",
        "registered_at": "2026-07-01T10:00:00+00:00", "status": "UNRESOLVED",
        "source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001",
    }
    record.update(overrides)
    return record


def _source_record(**overrides):
    record = {
        "ROWID": "row-record", "id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001",
        "source_system_id": "CCTNS_REPLICA", "external_id": "SYN-CASE-0001", "version": "1.0",
        "source_updated_at": "2026-07-01T08:00:00+00:00", "imported_at": "2026-07-01T09:00:00+00:00",
        "access_class": "RESTRICTED", "reliability_role": "Primary operational record",
        "freshness_state": "Fresh", "checksum": "a" * 64, "payload_json": "{\"synthetic\":true}",
    }
    record.update(overrides)
    return record


@pytest.fixture()
def fake():
    return FakeCatalystClient()


@pytest.fixture()
def repository(fake):
    return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


def _rows(fake, name, records):
    fake.register_rows(name.value, records)


def test_readonly_adapter_is_a_structural_repository_with_offline_capabilities(repository):
    assert repository.backend_name == "catalyst-readonly-offline"
    assert repository.capability().state.value == "available"
    assert repository.transaction_capability().state.value == "unavailable"
    assert repository.schema_version_capability().state.value == "unavailable"


def test_user_reads_preserve_contract_shape_and_filter_inactive(fake, repository):
    _rows(fake, CatalystQueryName.ACTIVE_USER_BY_USERNAME, [_user()])
    _rows(fake, CatalystQueryName.USER_BY_ID, [_user(active="false")])
    active = repository.find_active_user_by_username("investigator.demo")
    assert active == {"id": "SYN-USR-INV", "username": "investigator.demo", "password_hash": "safe-prototype-hash", "role": "INVESTIGATOR", "assigned_station": None, "assigned_district": None, "active": True, "_catalyst_rowid": "row-user"}
    assert repository.find_user_by_id("SYN-USR-INV")["active"] is False
    _rows(fake, CatalystQueryName.ACTIVE_USER_BY_USERNAME, [_user(active="false")])
    assert repository.find_active_user_by_username("investigator.demo") is None
    assert [request.query.name for request in fake.request_history] == [CatalystQueryName.ACTIVE_USER_BY_USERNAME, CatalystQueryName.USER_BY_ID, CatalystQueryName.ACTIVE_USER_BY_USERNAME]
    assert fake.request_history[0].parameters.values == {"username": "investigator.demo"}


@pytest.mark.parametrize("query, method, value", [
    (CatalystQueryName.USER_BY_ID, "find_user_by_id", "SYN-USR-INV"),
    (CatalystQueryName.CASE_BY_ID, "find_case_360_case", "SYN-CASE-0001"),
    (CatalystQueryName.SOURCE_PASSPORT_RECORD, "find_source_passport_record", "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001"),
])
def test_exact_reads_return_none_when_missing(fake, repository, query, method, value):
    _rows(fake, query, [])
    assert getattr(repository, method)(value) is None


@pytest.mark.parametrize(("query", "method", "value", "records"), [
    (CatalystQueryName.USER_BY_ID, "find_user_by_id", "SYN-USR-INV", [_user(), _user(ROWID="other")]),
    (CatalystQueryName.CASE_BY_ID, "find_case_360_case", "SYN-CASE-0001", [_case(), _case(ROWID="other")]),
    (CatalystQueryName.SOURCE_PASSPORT_RECORD, "find_source_passport_record", "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001", [{**_source_record(), "source_name": "CCTNS", "limitations": None}, {**_source_record(ROWID="other"), "source_name": "CCTNS", "limitations": None}]),
])
def test_exact_duplicate_rows_are_rejected(fake, repository, query, method, value, records):
    _rows(fake, query, records)
    with pytest.raises(ApiError) as error:
        getattr(repository, method)(value)
    assert error.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_source_system_reads_are_deterministic_and_complete(fake, repository):
    _rows(fake, CatalystQueryName.SOURCE_SYSTEM_LIST, [_source(id="Z_SOURCE", priority="P1"), _source(id="A_SOURCE", priority="P0")])
    _rows(fake, CatalystQueryName.SOURCE_SYSTEM_BY_ID, [_source()])
    listed = repository.list_source_systems()
    assert [row["id"] for row in listed] == ["A_SOURCE", "Z_SOURCE"]
    assert listed[0]["priority"] == "P0" and listed[0]["last_successful_sync"] is None
    assert repository.find_source_system("CCTNS_REPLICA")["connector_type"] == "SYNTHETIC"
    assert fake.request_history[0].parameters.values == {"limit": 50}


def test_case_and_source_record_exact_reads_keep_canonical_id_and_payload_string(fake, repository):
    _rows(fake, CatalystQueryName.CASE_BY_ID, [_case()])
    _rows(fake, CatalystQueryName.SOURCE_PASSPORT_RECORD, [{**_source_record(), "source_name": "CCTNS", "limitations": None}])
    assert repository.find_case_dna_case("SYN-CASE-0001")["id"] == "SYN-CASE-0001"
    source_record = repository.find_source_passport_record("SYN-SR-CCTNS_REPLICA-SYN-CASE-0001")
    assert source_record["payload_json"] == "{\"synthetic\":true}" and source_record["_catalyst_rowid"] == "row-record"


def test_schema_and_offline_health_handle_valid_empty_duplicate_and_failure_states(fake, repository):
    _rows(fake, CatalystQueryName.SCHEMA_VERSION, [{"version": "8", "ROWID": "schema"}])
    assert repository.schema_version() == 8
    assert repository.health_check() == "ok"
    _rows(fake, CatalystQueryName.SCHEMA_VERSION, [])
    assert repository.schema_version() == 0
    _rows(fake, CatalystQueryName.SCHEMA_VERSION, [{"version": "6"}, {"version": "5"}])
    with pytest.raises(ApiError) as duplicate:
        repository.schema_version()
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.fail_health("timeout", retryable=True)
    with pytest.raises(ApiError) as timeout:
        repository.health_check()
    assert (timeout.value.code, timeout.value.retryable) == ("CATALYST_TIMEOUT", True)


@pytest.mark.parametrize(("category", "retryable", "code"), [
    ("unavailable", True, "CATALYST_UNAVAILABLE"),
    ("authentication", False, "CATALYST_AUTHORIZATION_FAILED"),
])
def test_offline_health_translates_safe_failure_categories(fake, repository, category, retryable, code):
    fake.fail_health(category, retryable=retryable)
    with pytest.raises(ApiError) as error:
        repository.health_check()
    assert (error.value.code, error.value.retryable) == (code, retryable)
    fake.set_health_response({"status": "unexpected", "endpoint": "https://private.invalid"})
    with pytest.raises(ApiError) as malformed:
        repository.health_check()
    assert malformed.value.code == "CATALYST_MALFORMED_RESPONSE"
    assert "private" not in malformed.value.message.lower()


@pytest.mark.parametrize("method,args", [
    ("create_session", ("SYN-SES-1", "SYN-USR-INV", "hash", "2026-01-01T00:00:00+00:00", "2026-01-01T01:00:00+00:00")),
    ("revoke_session", ("SYN-SES-1", "2026-01-01T00:00:00+00:00")),
    ("upsert_source_systems", ([],)),
    ("create_import_job", ({}, [])),
    ("commit_import_rows", ("SYN-IMP-1", "2026-01-01T00:00:00+00:00", [])),
    ("create_investigation", ({},)),
    ("create_report_with_initial_version", ({}, {})),
    ("create_report_review_decision", ("SYN-RPT-1", 1, {}, "2026-01-01T00:00:00+00:00")),
    ("append_audit_event", (None,)),
])
def test_unsupported_operations_never_mutate_fake_or_fallback(fake, repository, method, args):
    with pytest.raises(ApiError) as error:
        getattr(repository, method)(*args)
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
    assert fake.request_history == []


def test_small_read_contract_matches_sqlite_records_after_normalizing_platform_row_id(app):
    sqlite = app.extensions["repository"]
    generate(sqlite, app.config, scale="test")
    user = sqlite.find_user_by_id("SYN-USR-INV")
    source = sqlite.find_source_system("CCTNS_REPLICA")
    case = sqlite.find_case_360_case("SYN-CASE-0001")
    source_record = sqlite.find_source_passport_record(case["source_record_id"])
    fake = FakeCatalystClient()
    _rows(fake, CatalystQueryName.USER_BY_ID, [{**user, "ROWID": "u"}])
    _rows(fake, CatalystQueryName.SOURCE_SYSTEM_LIST, [{**source, "ROWID": "s"}])
    _rows(fake, CatalystQueryName.SOURCE_SYSTEM_BY_ID, [{**source, "ROWID": "s"}])
    _rows(fake, CatalystQueryName.CASE_BY_ID, [{**case, "ROWID": "c"}])
    _rows(fake, CatalystQueryName.SOURCE_PASSPORT_RECORD, [{key: source_record[key] for key in ("id", "source_system_id", "external_id", "version", "source_updated_at", "imported_at", "access_class", "reliability_role", "freshness_state", "checksum", "payload_json", "source_name", "limitations")} | {"ROWID": "sr"}])
    _rows(fake, CatalystQueryName.SCHEMA_VERSION, [{"version": str(sqlite.schema_version())}])
    catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
    assert {key: value for key, value in catalyst.find_user_by_id(user["id"]).items() if key != "_catalyst_rowid"} == user
    assert {key: value for key, value in catalyst.find_source_system(source["id"]).items() if key != "_catalyst_rowid"} == source
    catalyst_case = {key: value for key, value in catalyst.find_case_360_case(case["id"]).items() if key != "_catalyst_rowid"}
    assert catalyst_case == {key: case[key] for key in catalyst_case}
    assert {key: value for key, value in catalyst.find_source_passport_record(source_record["id"]).items() if key != "_catalyst_rowid"} == {key: source_record[key] for key in ("id", "source_system_id", "external_id", "version", "source_updated_at", "imported_at", "access_class", "reliability_role", "freshness_state", "checksum", "payload_json", "source_name", "limitations")}
    assert catalyst.schema_version() == sqlite.schema_version()


def test_adapter_is_not_wired_to_application_and_has_no_transport_sqlite_or_credentials_path():
    source = Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8").lower()
    for forbidden in ("import sqlite", "sqlite3", "import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "credentials_path", "os.getenv"):
        assert forbidden not in source
    production = Path("backend/anvaya")
    for path in list((production / "services").glob("*.py")) + list((production / "api").glob("*.py")):
        assert "CatalystReadOnlyRepository" not in path.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True})
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().find_user_by_id("SYN-USR-INV")
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
