"""Offline fake-backed SEARCH candidate contract tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.generator import generate
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient


def _candidate(**overrides):
    row = {
        "ROWID": "row-search", "id": "SYN-CASE-0001", "fir_number": "SYN-FIR-000001",
        "crime_number": "SYN-CRIME-00001", "station_id": "SYN-STN-01", "district_id": "SYN-DST-01",
        "offence": "CHAIN_SNATCHING", "incident_at": "2026-07-10T08:00:00+00:00",
        "registered_at": "2026-07-10T10:00:00+00:00", "status": "UNRESOLVED",
        "source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0001", "freshness_state": "Fresh",
        "source_system_id": "CCTNS_REPLICA", "reliability_role": "Primary operational record",
        "access_class": "RESTRICTED", "raw_payload": "must-not-leak",
    }
    row.update(overrides)
    return row


@pytest.fixture()
def fake():
    return FakeCatalystClient()


@pytest.fixture()
def repository(fake):
    return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


def _rows(fake, rows):
    fake.register_rows(CatalystQueryName.SEARCH_CASE_CANDIDATES.value, rows)


def test_search_exact_identifier_filters_and_shape_are_fixed(fake, repository):
    _rows(fake, [_candidate()])
    for field, value in (("case_identifier", "SYN-CASE-0001"), ("case_identifier", "SYN-FIR-000001"), ("case_identifier", "SYN-CRIME-00001")):
        result = repository.search_case_candidates(CaseSearchFilter(**{field: value}, source_system_ids=("CCTNS_REPLICA",)))
        assert result[0]["id"] == "SYN-CASE-0001"
        assert result[0]["_catalyst_rowid"] == "row-search"
        assert "raw_payload" not in result[0]
    request = fake.request_history[-1]
    assert request.query.name is CatalystQueryName.SEARCH_CASE_CANDIDATES
    assert request.parameters.values["case_identifier"] == "SYN-CRIME-00001"
    assert request.parameters.values["source_system_ids"] == ("CCTNS_REPLICA",)
    assert request.parameters.values["limit"] == 25 and request.parameters.values["offset"] == 0


@pytest.mark.parametrize(("filters", "row"), [
    (CaseSearchFilter(offence="CHAIN_SNATCHING"), _candidate()),
    (CaseSearchFilter(status="UNRESOLVED"), _candidate()),
    (CaseSearchFilter(location="SYN-STN-01"), _candidate()),
    (CaseSearchFilter(location="syn-dst-01"), _candidate()),
    (CaseSearchFilter(date_from="2026-07-10"), _candidate()),
    (CaseSearchFilter(date_to="2026-07-10"), _candidate()),
    (CaseSearchFilter(date_from="2026-07-10", date_to="2026-07-10"), _candidate()),
    (CaseSearchFilter(phone="SYN-PHONE-000001"), _candidate()),
    (CaseSearchFilter(imei="SYN-IMEI-000000000001"), _candidate()),
    (CaseSearchFilter(vehicle_registration="SYN-REG-000001"), _candidate()),
])
def test_search_fixed_template_accepts_current_single_filter_categories(fake, repository, filters, row):
    _rows(fake, [row])
    result = repository.search_case_candidates(filters)
    assert result and result[0]["id"] == "SYN-CASE-0001"


def test_search_defensively_rejects_overbroad_visible_scope_and_filter_rows(fake, repository):
    cases = [
        (CaseSearchFilter(offence="ROBBERY"), _candidate(), "offence"),
        (CaseSearchFilter(status="RESOLVED"), _candidate(), "status"),
        (CaseSearchFilter(location="SYN-STN-99"), _candidate(), "location"),
        (CaseSearchFilter(date_from="2026-07-11"), _candidate(), "date"),
        (CaseSearchFilter(case_identifier="SYN-FIR-999999"), _candidate(), "identifier"),
        (CaseSearchFilter(source_system_ids=("FORENSICS_REPLICA",)), _candidate(), "source"),
    ]
    for filters, row, _reason in cases:
        _rows(fake, [row])
        with pytest.raises(ApiError) as error:
            repository.search_case_candidates(filters)
        assert error.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_search_order_pagination_caps_and_missing_results_are_deterministic(fake, repository):
    later = _candidate(id="SYN-CASE-0002", incident_at="2026-07-11T08:00:00+00:00", fir_number="SYN-FIR-000002", crime_number="SYN-CRIME-00002")
    earlier_same_time = _candidate(id="SYN-CASE-0000", incident_at="2026-07-10T08:00:00+00:00", fir_number="SYN-FIR-000000", crime_number="SYN-CRIME-00000")
    _rows(fake, [_candidate(), earlier_same_time, later])
    result = repository.search_case_candidates(CaseSearchFilter(limit=3, source_system_ids=("CCTNS_REPLICA",)))
    assert [item["id"] for item in result] == ["SYN-CASE-0002", "SYN-CASE-0000", "SYN-CASE-0001"]
    _rows(fake, [])
    assert repository.search_case_candidates(CaseSearchFilter(case_identifier="SYN-CASE-MISSING")) == []
    _rows(fake, [_candidate(), later])
    with pytest.raises(ApiError) as over_limit:
        repository.search_case_candidates(CaseSearchFilter(limit=1, offset=1))
    assert over_limit.value.code == "CATALYST_MALFORMED_RESPONSE"
    assert fake.request_history[-1].parameters.values["offset"] == 1
    _rows(fake, [_candidate() for _ in range(26)])
    with pytest.raises(ApiError) as oversized:
        repository.search_case_candidates(CaseSearchFilter())
    assert oversized.value.code == "CATALYST_MALFORMED_RESPONSE"
    _rows(fake, [_candidate(), _candidate(ROWID="row-duplicate", incident_at="2026-07-09T08:00:00+00:00")])
    with pytest.raises(ApiError) as duplicate:
        repository.search_case_candidates(CaseSearchFilter(limit=2))
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_search_rejects_bad_filter_object_unsupported_entity_combination_and_malformed_row(fake, repository):
    with pytest.raises(ApiError) as invalid:
        repository.search_case_candidates({})  # type: ignore[arg-type]
    assert invalid.value.code == "CATALYST_INVALID_PARAMETERS"
    with pytest.raises(ApiError) as unsupported:
        repository.search_case_candidates(CaseSearchFilter(phone="SYN-PHONE-000001", imei="SYN-IMEI-000000000001"))
    assert unsupported.value.code == "CATALYST_QUERY_UNSUPPORTED"
    _rows(fake, [_candidate(id=None)])
    with pytest.raises(ApiError) as malformed:
        repository.search_case_candidates(CaseSearchFilter())
    assert malformed.value.code == "CATALYST_MALFORMED_RESPONSE"
    with pytest.raises(ApiError) as bad_date:
        repository.search_case_candidates(CaseSearchFilter(date_from="not-a-date"))
    assert bad_date.value.code == "CATALYST_INVALID_PARAMETERS"


@pytest.mark.parametrize(("category", "retryable", "code"), [
    ("timeout", True, "CATALYST_TIMEOUT"),
    ("unavailable", True, "CATALYST_UNAVAILABLE"),
    ("authentication", False, "CATALYST_AUTHORIZATION_FAILED"),
])
def test_search_client_failures_are_safe(fake, repository, category, retryable, code):
    fake.fail(CatalystQueryName.SEARCH_CASE_CANDIDATES.value, category, retryable)
    with pytest.raises(ApiError) as error:
        repository.search_case_candidates(CaseSearchFilter())
    assert (error.value.code, error.value.retryable) == (code, retryable)
    assert all(value not in error.value.message.lower() for value in ("http", "secret", "credential", "stack"))


def test_search_sqlite_parity_for_representative_fixed_filters(app):
    sqlite = app.extensions["repository"]
    generate(sqlite, app.config, "test")
    filters = [
        CaseSearchFilter(case_identifier="SYN-CASE-0001", source_system_ids=("CCTNS_REPLICA",)),
        CaseSearchFilter(case_identifier="SYN-FIR-000001", source_system_ids=("CCTNS_REPLICA",)),
        CaseSearchFilter(case_identifier="SYN-CRIME-00001", source_system_ids=("CCTNS_REPLICA",)),
        CaseSearchFilter(offence="CHAIN_SNATCHING", status="UNRESOLVED", source_system_ids=("CCTNS_REPLICA",), limit=3),
        CaseSearchFilter(location="SYN-STN-01", source_system_ids=("CCTNS_REPLICA",)),
        CaseSearchFilter(date_from="2026-03-01", date_to="2026-07-11", source_system_ids=("CCTNS_REPLICA",), limit=2),
        CaseSearchFilter(imei="SYN-IMEI-000000000001", source_system_ids=("CCTNS_REPLICA",)),
    ]
    for filters_item in filters:
        expected = sqlite.search_case_candidates(filters_item)
        fake = FakeCatalystClient()
        _rows(fake, [{**row, "ROWID": f"row-{index}"} for index, row in enumerate(expected)])
        catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
        actual = catalyst.search_case_candidates(filters_item)
        assert [{key: value for key, value in row.items() if key != "_catalyst_rowid"} for row in actual] == expected


def test_search_adapter_is_unwired_and_uses_no_transport_sdk_credentials_or_raw_query_passthrough():
    adapter = Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8").lower()
    templates = Path("backend/anvaya/repositories/catalyst_templates.py").read_text(encoding="utf-8")
    for forbidden in ("import sqlite", "sqlite3", "import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "credentials_path", "os.getenv"):
        assert forbidden not in adapter
    assert "SELECT" not in Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8")
    assert "SEARCH_CASE_CANDIDATES" in templates
    for path in list(Path("backend/anvaya/services").glob("*.py")) + list(Path("backend/anvaya/api").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "CatalystReadOnlyRepository" not in text and "FakeCatalystClient" not in text
    with pytest.raises(ValueError):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True})
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().search_case_candidates(CaseSearchFilter())
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
