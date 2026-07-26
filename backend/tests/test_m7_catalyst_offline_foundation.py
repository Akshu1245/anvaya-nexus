from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.platform.catalyst_errors import CatalystClientFailure, translate_catalyst_failure
from backend.anvaya.repositories.catalyst_binding import bind_parameters
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_rows import extract_rows, normalize_row
from backend.anvaya.repositories.catalyst_templates import (
    CatalystParameterDefinition, CatalystParameterKind, CatalystQueryName, CatalystQueryTemplate,
    CatalystOperationKind, CatalystTemplateRegistry, DEFAULT_CATALYST_TEMPLATES,
)
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient


def _user_row(**overrides):
    row = {"ROWID": "9001", "id": "SYN-USR-INV", "username": "investigator.demo", "password_hash": "prototype-hash", "role": "INVESTIGATOR", "assigned_station": "SYN-STN-01", "assigned_district": "SYN-DST-01", "active": "true"}
    row.update(overrides)
    return row


def _source_row(**overrides):
    row = {"ROWID": "9002", "id": "CCTNS_REPLICA", "name": "CCTNS Replica", "source_tier": "PRIMARY", "access_class": "RESTRICTED", "reliability_role": "Primary operational record", "status": "Fresh", "last_successful_sync": None, "freshness_threshold_hours": "24", "version": "1.0", "connector_type": "SYNTHETIC", "description": "Synthetic source", "priority": "1", "internal_url": "must-not-leak"}
    row.update(overrides)
    return row


def _case_row(**overrides):
    row = {"ROWID": "9003", "id": "SYN-CASE-0001", "fir_number": "SYN-FIR-000001", "crime_number": "SYN-CRIME-00001", "station_id": "SYN-STN-01", "district_id": "SYN-DST-01", "offence": "CHAIN_SNATCHING", "incident_at": "2026-07-01T08:00:00+00:00", "registered_at": "2026-07-01T10:00:00+00:00", "status": "UNRESOLVED", "source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001"}
    row.update(overrides)
    return row


def _source_record_row(**overrides):
    row = {"ROWID": "9004", "id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001", "source_system_id": "CCTNS_REPLICA", "external_id": "SYN-CASE-0001", "version": "1.0", "source_updated_at": "2026-07-01T08:00:00+00:00", "imported_at": "2026-07-01T08:00:00+00:00", "access_class": "RESTRICTED", "reliability_role": "Primary operational record", "freshness_state": "Fresh", "checksum": "a" * 64, "payload_json": "{}"}
    row.update(overrides)
    return row


def test_registry_is_fixed_immutable_and_rejects_unknown_or_duplicate_names():
    template = DEFAULT_CATALYST_TEMPLATES.get(CatalystQueryName.USER_BY_ID)
    assert template.name is CatalystQueryName.USER_BY_ID
    with pytest.raises(FrozenInstanceError):
        template.text = "SELECT arbitrary"  # type: ignore[misc]
    with pytest.raises(ApiError, match="not supported"):
        DEFAULT_CATALYST_TEMPLATES.get("SELECT * FROM users")
    with pytest.raises(ValueError, match="Duplicate"):
        CatalystTemplateRegistry((template, template))


@pytest.mark.parametrize(("name", "parameters"), [
    (CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV"}),
    (CatalystQueryName.USER_BY_USERNAME, {"username": "investigator.demo"}),
    (CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 25}),
    (CatalystQueryName.SCHEMA_VERSION, {}),
])
def test_logical_parameter_binding_accepts_only_declared_values(name, parameters):
    template = DEFAULT_CATALYST_TEMPLATES.get(name)
    bound = bind_parameters(template, parameters)
    assert dict(bound.values) == parameters


@pytest.mark.parametrize(("name", "parameters"), [
    (CatalystQueryName.USER_BY_ID, {}),
    (CatalystQueryName.USER_BY_ID, {"id": "bad id"}),
    (CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV", "order": "id DESC"}),
    (CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 51}),
    (CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 0}),
])
def test_binding_rejects_missing_extra_invalid_and_excessive_values(name, parameters):
    with pytest.raises(ApiError) as error:
        bind_parameters(DEFAULT_CATALYST_TEMPLATES.get(name), parameters)
    assert error.value.code == "CATALYST_INVALID_PARAMETERS"


def test_binding_validates_timestamps_offsets_nulls_and_deduplicated_lists():
    template = CatalystQueryTemplate(
        CatalystQueryName.USER_BY_ID, CatalystOperationKind.READ, "offline", (
            CatalystParameterDefinition("when", CatalystParameterKind.TIMESTAMP),
            CatalystParameterDefinition("offset", CatalystParameterKind.OFFSET),
            CatalystParameterDefinition("ids", CatalystParameterKind.STRING_LIST),
            CatalystParameterDefinition("optional", CatalystParameterKind.STRING, required=False, allow_null=True),
        ), "user", "fixed", 1, "unverified", "test only",
    )
    bound = bind_parameters(template, {"when": "2026-07-13T10:00:00+00:00", "offset": 0, "ids": ["SYN-USR-INV", "SYN-USR-INV"], "optional": None})
    assert bound.values["ids"] == ("SYN-USR-INV",)
    for invalid in ("not-a-time", "2026-01-01"):
        with pytest.raises(ApiError):
            bind_parameters(template, {"when": invalid, "offset": 0, "ids": ["SYN-USR-INV"]})
    with pytest.raises(ApiError):
        bind_parameters(template, {"when": "2026-07-13T10:00:00+00:00", "offset": -1, "ids": ["SYN-USR-INV"]})


def test_binding_never_interpolates_user_value_into_template_text():
    template = DEFAULT_CATALYST_TEMPLATES.get(CatalystQueryName.USER_BY_USERNAME)
    untrusted = "x' OR 1=1 --"
    bound = bind_parameters(template, {"username": untrusted})
    assert untrusted not in template.text
    assert bound.values["username"] == untrusted


@pytest.mark.parametrize(("shape", "row", "expected"), [
    ("user", _user_row(), {"id": "SYN-USR-INV", "password_hash": "prototype-hash", "active": True, "_catalyst_rowid": "9001"}),
    ("source_system", _source_row(), {"id": "CCTNS_REPLICA", "freshness_threshold_hours": 24, "priority": "1"}),
    ("case", _case_row(), {"id": "SYN-CASE-0001", "incident_at": "2026-07-01T08:00:00+00:00"}),
    ("source_record", _source_record_row(), {"id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001", "checksum": "a" * 64}),
    ("schema_state", {"version": "4", "ROWID": "99"}, {"version": 4, "_catalyst_rowid": "99"}),
])
def test_row_normalization_keeps_canonical_ids_and_isolates_platform_fields(shape, row, expected):
    normalized = normalize_row(shape, row)
    for key, value in expected.items():
        assert normalized[key] == value
    assert "internal_url" not in normalized


def test_row_normalization_rejects_missing_required_field_and_bad_envelope():
    with pytest.raises(ApiError) as error:
        normalize_row("user", _user_row(id=None))
    assert error.value.code == "CATALYST_MALFORMED_RESPONSE"
    with pytest.raises(ApiError):
        extract_rows({"status": "success", "data": {"rows": "not-list"}})


def test_gateway_executes_only_registered_fixed_reads_and_records_request_history():
    fake = FakeCatalystClient()
    fake.register_rows(CatalystQueryName.USER_BY_ID.value, [_user_row()])
    rows = CatalystReadGateway(fake).read(CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV"})
    assert rows == [{"id": "SYN-USR-INV", "username": "investigator.demo", "password_hash": "prototype-hash", "role": "INVESTIGATOR", "assigned_station": "SYN-STN-01", "assigned_district": "SYN-DST-01", "active": True, "_catalyst_rowid": "9001"}]
    assert fake.request_history[0].query.name is CatalystQueryName.USER_BY_ID
    assert fake.request_history[0].parameters.values == {"id": "SYN-USR-INV"}


def test_gateway_handles_empty_malformed_oversized_and_client_failures_safely():
    fake = FakeCatalystClient()
    gateway = CatalystReadGateway(fake)
    fake.register_rows(CatalystQueryName.USER_BY_ID.value, [])
    assert gateway.read(CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV"}) == []
    fake.register_rows(CatalystQueryName.USER_BY_ID.value, [_user_row(), _user_row(id="SYN-USR-ANA")])
    with pytest.raises(ApiError) as oversized:
        gateway.read(CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV"})
    assert oversized.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.fail(CatalystQueryName.USER_BY_ID.value, "timeout", retryable=True)
    with pytest.raises(ApiError) as timeout:
        gateway.read(CatalystQueryName.USER_BY_ID, {"id": "SYN-USR-INV"})
    assert (timeout.value.code, timeout.value.retryable) == ("CATALYST_TIMEOUT", True)


@pytest.mark.parametrize(("category", "code", "retryable"), [
    ("unavailable", "CATALYST_UNAVAILABLE", True),
    ("rate_limited", "CATALYST_RATE_LIMITED", True),
    ("authentication", "CATALYST_AUTHORIZATION_FAILED", False),
    ("conflict", "CATALYST_CONFLICT", False),
    ("malformed_response", "CATALYST_MALFORMED_RESPONSE", True),
    ("not_implemented", "CATALYST_NOT_IMPLEMENTED", False),
])
def test_safe_error_translation_has_no_transport_or_secret_leakage(category, code, retryable):
    error = translate_catalyst_failure(CatalystClientFailure(category, retryable, "https://private.invalid Authorization: secret stack trace"))
    assert (error.code, error.retryable) == (code, retryable)
    assert "private" not in error.message.lower() and "secret" not in error.message.lower() and "stack" not in error.message.lower()


def test_fake_is_offline_and_has_no_sqlite_or_network_fallback():
    source = Path(__file__).parents[0] / "fakes" / "fake_catalyst_client.py"
    text = source.read_text(encoding="utf-8")
    assert "requests" not in text and "urllib" not in text and "sqlite" not in text and "http" not in text
    fake = FakeCatalystClient()
    with pytest.raises(CatalystClientFailure) as error:
        fake.execute_read(type("Request", (), {"query": type("Query", (), {"name": type("Name", (), {"value": "unexpected"})()})()})())
    assert error.value.category == "unsupported_query"


def test_offline_foundation_imports_no_transport_sdk_or_credential_reader():
    paths = [
        Path("backend/anvaya/platform/catalyst_client.py"),
        Path("backend/anvaya/platform/catalyst_errors.py"),
        Path("backend/anvaya/repositories/catalyst_templates.py"),
        Path("backend/anvaya/repositories/catalyst_binding.py"),
        Path("backend/anvaya/repositories/catalyst_rows.py"),
        Path("backend/anvaya/repositories/catalyst_gateway.py"),
        Path("backend/tests/fakes/fake_catalyst_client.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()
    for forbidden in ("import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "os.getenv", "credentials_path"):
        assert forbidden not in text


def test_gateway_not_wired_to_services_or_repository_and_placeholder_stays_unavailable(app):
    production = Path("backend/anvaya")
    for path in list((production / "services").glob("*.py")) + list((production / "api").glob("*.py")):
        assert "CatalystReadGateway" not in path.read_text(encoding="utf-8")
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().find_user_by_id("SYN-USR-INV")
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
    assert app.extensions["platform_adapters"].repository.backend_name == "sqlite"
