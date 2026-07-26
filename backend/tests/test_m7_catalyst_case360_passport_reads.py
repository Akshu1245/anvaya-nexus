"""Offline fake-client contracts for Case 360 and Source Passport reads."""
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


CASE_ID = "SYN-CASE-0001"
SOURCE_ID = "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001"


def _entity(**changes):
    row = {"ROWID": "entity-row", "edge_id": "SYN-EDGE-01", "case_id": CASE_ID, "target_type": "PHONE", "target_id": "SYN-PHONE-01", "edge_source_record_id": SOURCE_ID, "value": "SYN-9000000001", "entity_source_record_id": SOURCE_ID, "raw_payload": "never"}
    row.update(changes)
    return row


def _evidence(**changes):
    row = {"ROWID": "evidence-row", "id": "SYN-EVD-01", "case_id": CASE_ID, "evidence_type": "SYNTHETIC_ITEM", "description": "Synthetic evidence", "status": "AVAILABLE", "sensitivity": "RESTRICTED", "source_record_id": SOURCE_ID}
    row.update(changes)
    return row


def _forensic(**changes):
    row = {"ROWID": "forensic-row", "id": "SYN-FOR-01", "case_id": CASE_ID, "event_type": "DEVICE_METADATA", "occurred_at": "2026-07-10T08:00:00+00:00", "result_status": "SYNTHETIC_RESULT", "source_record_id": SOURCE_ID}
    row.update(changes)
    return row


def _issue(**changes):
    row = {"ROWID": "issue-row", "id": "SYN-ISSUE-01", "case_id": CASE_ID, "issue_type": "missing_source", "severity": "SEEDED", "description": "Synthetic issue", "source_record_ids_json": "[]", "status": "OPEN"}
    row.update(changes)
    return row


def _passport(**changes):
    row = {"ROWID": "passport-row", "id": SOURCE_ID, "source_system_id": "CCTNS_REPLICA", "external_id": "SYN-CASE-0001", "version": "1", "source_updated_at": "2026-07-10T08:00:00+00:00", "imported_at": "2026-07-10T09:00:00+00:00", "access_class": "RESTRICTED", "reliability_role": "Primary operational record", "freshness_state": "Fresh", "checksum": "synthetic-checksum", "payload_json": "{\"synthetic\":true}", "source_name": "CCTNS replica", "limitations": "Synthetic data only", "endpoint": "never"}
    row.update(changes)
    return row


def _transformation(**changes):
    row = {"ROWID": "transform-row", "operation": "NORMALIZE", "source_field": "fir", "target_field": "fir_number", "rule_version": "v1", "occurred_at": "2026-07-10T08:00:00+00:00", "outcome": "APPLIED", "secret": "never"}
    row.update(changes)
    return row


@pytest.fixture()
def fake():
    return FakeCatalystClient()


@pytest.fixture()
def repository(fake):
    return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


@pytest.mark.parametrize(("query", "method", "factory", "id_field"), [
    (CatalystQueryName.CASE_360_ENTITIES, "list_case_360_entities", _entity, "edge_id"),
    (CatalystQueryName.CASE_360_EVIDENCE, "list_case_360_evidence", _evidence, "id"),
    (CatalystQueryName.CASE_360_FORENSICS, "list_case_360_forensics", _forensic, "id"),
    (CatalystQueryName.CASE_360_TRUST_ISSUES, "list_case_360_trust_issues", _issue, "id"),
])
def test_case360_sections_are_scoped_deterministic_and_safe(fake, repository, query, method, factory, id_field):
    later = factory(**{id_field: "SYN-Z"})
    fake.register_rows(query.value, [later, factory()])
    result = getattr(repository, method)(CASE_ID)
    assert [row[id_field] for row in result] == sorted(row[id_field] for row in result)
    assert "raw_payload" not in result[0] and "_catalyst_rowid" in result[0]
    assert fake.request_history[-1].parameters.values == {"case_id": CASE_ID}
    fake.register_rows(query.value, [factory(case_id="SYN-CASE-OTHER")])
    with pytest.raises(ApiError, match="invalid response") as error:
        getattr(repository, method)(CASE_ID)
    assert error.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_entity_allowlist_null_value_and_duplicates(fake, repository):
    fake.register_rows(CatalystQueryName.CASE_360_ENTITIES.value, [_entity(target_type="PERSON", value=None), _entity(edge_id="SYN-EDGE-02", target_type="LOCATION", target_id="SYN-LOC-01", value="Jayanagar")])
    assert [row["target_type"] for row in repository.list_case_360_entities(CASE_ID)] == ["LOCATION"]
    fake.register_rows(CatalystQueryName.CASE_360_ENTITIES.value, [_entity(target_type="ORGANISATION")])
    with pytest.raises(ApiError) as invalid_type:
        repository.list_case_360_entities(CASE_ID)
    assert invalid_type.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.CASE_360_ENTITIES.value, [_entity(), _entity(ROWID="another")])
    with pytest.raises(ApiError) as duplicate:
        repository.list_case_360_entities(CASE_ID)
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_passport_and_ordered_transformations_are_fixed_and_safe(fake, repository):
    fake.register_rows(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, [_passport()])
    record = repository.find_source_passport_record(SOURCE_ID)
    assert record and record["payload_json"] == '{"synthetic":true}' and record["source_name"] == "CCTNS replica"
    assert "endpoint" not in record and record["_catalyst_rowid"] == "passport-row"
    fake.register_rows(CatalystQueryName.SOURCE_TRANSFORMATIONS.value, [_transformation(operation="Z", occurred_at="2026-07-11T08:00:00+00:00"), _transformation(operation="A")])
    history = repository.list_source_transformations(SOURCE_ID)
    assert [(row["occurred_at"], row["operation"]) for row in history] == [("2026-07-10T08:00:00+00:00", "A"), ("2026-07-11T08:00:00+00:00", "Z")]
    assert "secret" not in history[0]
    fake.register_rows(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, [])
    assert repository.find_source_passport_record("SYN-SR-MISSING") is None
    fake.register_rows(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, [_passport(), _passport(ROWID="duplicate")])
    with pytest.raises(ApiError) as duplicate:
        repository.find_source_passport_record(SOURCE_ID)
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, [_passport(id="SYN-SR-OTHER")])
    with pytest.raises(ApiError) as cross_record:
        repository.find_source_passport_record(SOURCE_ID)
    assert cross_record.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_case360_passport_failures_and_unsupported_operations_are_safe(fake, repository):
    fake.fail(CatalystQueryName.CASE_360_EVIDENCE.value, "timeout", True)
    with pytest.raises(ApiError) as timeout:
        repository.list_case_360_evidence(CASE_ID)
    assert (timeout.value.code, timeout.value.retryable) == ("CATALYST_TIMEOUT", True)
    fake.fail(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, "authentication")
    with pytest.raises(ApiError) as auth:
        repository.find_source_passport_record(SOURCE_ID)
    assert auth.value.code == "CATALYST_AUTHORIZATION_FAILED"
    with pytest.raises(ApiError) as unsupported:
        repository.create_session({})
    assert unsupported.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_case360_passport_sqlite_parity(app):
    sqlite = app.extensions["repository"]
    generate(sqlite, app.config, "test")
    case = sqlite.find_case_360_case(CASE_ID)
    source_id = case["source_record_id"]
    fake = FakeCatalystClient()
    fake.register_rows(CatalystQueryName.CASE_BY_ID.value, [{**case, "ROWID": "case"}])
    fake.register_rows(CatalystQueryName.CASE_360_ENTITIES.value, [{**row, "case_id": CASE_ID, "ROWID": str(index)} for index, row in enumerate(sqlite.list_case_360_entities(CASE_ID))])
    fake.register_rows(CatalystQueryName.CASE_360_EVIDENCE.value, [{**row, "ROWID": str(index)} for index, row in enumerate(sqlite.list_case_360_evidence(CASE_ID))])
    fake.register_rows(CatalystQueryName.CASE_360_FORENSICS.value, [{**row, "ROWID": str(index)} for index, row in enumerate(sqlite.list_case_360_forensics(CASE_ID))])
    fake.register_rows(CatalystQueryName.CASE_360_TRUST_ISSUES.value, [{**row, "ROWID": str(index)} for index, row in enumerate(sqlite.list_case_360_trust_issues(CASE_ID))])
    record = sqlite.find_source_passport_record(source_id)
    fake.register_rows(CatalystQueryName.SOURCE_PASSPORT_RECORD.value, [{**record, "ROWID": "record"}])
    fake.register_rows(CatalystQueryName.SOURCE_TRANSFORMATIONS.value, [{**row, "ROWID": str(index)} for index, row in enumerate(sqlite.list_source_transformations(source_id))])
    catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
    clean = lambda rows: [{key: value for key, value in row.items() if key != "_catalyst_rowid"} for row in rows]
    assert clean(catalyst.list_case_360_entities(CASE_ID)) == sqlite.list_case_360_entities(CASE_ID)
    assert clean(catalyst.list_case_360_evidence(CASE_ID)) == sqlite.list_case_360_evidence(CASE_ID)
    assert clean(catalyst.list_case_360_forensics(CASE_ID)) == sqlite.list_case_360_forensics(CASE_ID)
    assert clean(catalyst.list_case_360_trust_issues(CASE_ID)) == sqlite.list_case_360_trust_issues(CASE_ID)
    assert clean(catalyst.list_source_transformations(source_id)) == sqlite.list_source_transformations(source_id)


def test_case360_adapter_is_unwired_and_no_transport_sdk_credentials_or_query_passthrough():
    adapter = Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8").lower()
    for forbidden in ("import sqlite", "sqlite3", "import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "credentials_path", "os.getenv"):
        assert forbidden not in adapter
    assert "SELECT" not in Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True})
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().list_case_360_entities(CASE_ID)
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
