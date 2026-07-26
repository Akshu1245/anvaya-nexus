"""Offline fake-client contracts for DISCOVER candidates and stored graph edges."""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RelationshipPathRequest
from backend.anvaya.services.generator import generate
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient


def _candidate(**overrides):
    row = {
        "ROWID": "row-discovery", "base_case_id": "SYN-CASE-0001", "target_type": "DEVICE",
        "relationship_type": "SHARED_IMEI", "edge_source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-EDGE-GOLDEN-1",
        "candidate_id": "SYN-CASE-0002", "link_source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-EDGE-GOLDEN-2",
        "id": "SYN-CASE-0002", "fir_number": "SYN-FIR-000002", "crime_number": "SYN-CRIME-00002",
        "station_id": "SYN-STN-02", "district_id": "SYN-DST-02", "offence": "CHAIN_SNATCHING",
        "incident_at": "2026-07-11T08:00:00+00:00", "registered_at": "2026-07-11T10:00:00+00:00",
        "status": "UNRESOLVED", "source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-CASE-0002",
        "freshness_state": "Fresh", "source_system_id": "CCTNS_REPLICA",
        "reliability_role": "Primary operational record", "access_class": "RESTRICTED", "payload_json": "must-not-leak",
    }
    row.update(overrides)
    return row


def _edge(**overrides):
    row = {
        "ROWID": "row-edge", "id": "SYN-EDGE-GOLDEN-1", "source_type": "CASE", "source_id": "SYN-CASE-0001",
        "target_type": "DEVICE", "target_id": "SYN-DEV-0001", "relationship_type": "SHARED_IMEI",
        "edge_class": "DIRECT_EVIDENCE", "source_record_id": "SYN-SR-CCTNS_REPLICA-SYN-EDGE-GOLDEN-1",
        "freshness_state": "Fresh", "reliability_role": "Primary operational record", "access_class": "RESTRICTED",
        "source_system_id": "CCTNS_REPLICA", "raw_transport": "must-not-leak",
    }
    row.update(overrides)
    return row


@pytest.fixture()
def fake():
    return FakeCatalystClient()


@pytest.fixture()
def repository(fake):
    return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


def _candidate_rows(fake, rows):
    fake.register_rows(CatalystQueryName.DISCOVERY_CANDIDATES.value, rows)


def _edge_rows(fake, rows):
    fake.register_rows(CatalystQueryName.RELATIONSHIP_EDGES.value, rows)


@pytest.mark.parametrize(("target_type", "relationship_type"), [
    ("PHONE", "RECORDED_PHONE"), ("DEVICE", "SHARED_IMEI"), ("VEHICLE", "RECORDED_VEHICLE"),
])
def test_discovery_candidate_reads_preserve_fixed_sqlite_projection(fake, repository, target_type, relationship_type):
    _candidate_rows(fake, [_candidate(target_type=target_type, relationship_type=relationship_type)])
    request = DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",))
    result = repository.list_discovery_candidates(request)
    assert result[0]["candidate_id"] == "SYN-CASE-0002" and result[0]["_catalyst_rowid"] == "row-discovery"
    assert "payload_json" not in result[0]
    assert fake.request_history[-1].query.name is CatalystQueryName.DISCOVERY_CANDIDATES
    assert fake.request_history[-1].parameters.values == {"seed_case_ids": ("SYN-CASE-0001",), "source_system_ids": ("CCTNS_REPLICA",), "limit": 25, "offset": 0}


def test_discovery_scope_order_cap_and_current_duplicate_behavior(fake, repository):
    later = _candidate(id="SYN-CASE-0003", candidate_id="SYN-CASE-0003", incident_at="2026-07-12T08:00:00+00:00")
    duplicate_candidate = _candidate(ROWID="relationship-two", relationship_type="RECORDED_DEVICE")
    _candidate_rows(fake, [_candidate(), duplicate_candidate, later])
    request = DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=3)
    result = repository.list_discovery_candidates(request)
    assert [row["id"] for row in result] == ["SYN-CASE-0003", "SYN-CASE-0002", "SYN-CASE-0002"]
    _candidate_rows(fake, [])
    assert repository.list_discovery_candidates(request) == []
    _candidate_rows(fake, [_candidate(source_system_id="VEHICLE_REPLICA")])
    with pytest.raises(ApiError) as wrong_source:
        repository.list_discovery_candidates(request)
    assert wrong_source.value.code == "CATALYST_MALFORMED_RESPONSE"
    _candidate_rows(fake, [_candidate(base_case_id="SYN-CASE-OTHER")])
    with pytest.raises(ApiError) as overbroad:
        repository.list_discovery_candidates(request)
    assert overbroad.value.code == "CATALYST_MALFORMED_RESPONSE"
    _candidate_rows(fake, [_candidate() for _ in range(26)])
    with pytest.raises(ApiError) as oversized:
        repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=25, offset=1))
    assert oversized.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_discovery_wrong_request_and_malformed_candidate_are_rejected(fake, repository):
    with pytest.raises(ApiError) as invalid:
        repository.list_discovery_candidates({})  # type: ignore[arg-type]
    assert invalid.value.code == "CATALYST_INVALID_PARAMETERS"
    _candidate_rows(fake, [_candidate(candidate_id="SYN-CASE-0001", id="SYN-CASE-0001")])
    with pytest.raises(ApiError) as self_candidate:
        repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",)))
    assert self_candidate.value.code == "CATALYST_MALFORMED_RESPONSE"
    _candidate_rows(fake, [_candidate(id=None)])
    with pytest.raises(ApiError) as malformed:
        repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",)))
    assert malformed.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_relationship_edges_are_allowlisted_source_scoped_and_deterministic(fake, repository):
    second = _edge(id="SYN-EDGE-A", relationship_type="RECORDED_DEVICE")
    _edge_rows(fake, [_edge(), second])
    request = RelationshipPathRequest(relationship_types=("SHARED_IMEI", "RECORDED_DEVICE"))
    result = repository.list_relationship_edges(request)
    assert [edge["id"] for edge in result] == ["SYN-EDGE-A", "SYN-EDGE-GOLDEN-1"]
    assert "raw_transport" not in result[0] and result[0]["_catalyst_rowid"] == "row-edge"
    assert fake.request_history[-1].parameters.values == {"relationship_types": ("SHARED_IMEI", "RECORDED_DEVICE"), "source_system_ids": ("CCTNS_REPLICA",), "edge_limit": 200}
    _edge_rows(fake, [])
    assert repository.list_relationship_edges(request) == []


def test_relationship_edge_rejections_and_current_self_loop_behavior(fake, repository):
    request = RelationshipPathRequest(relationship_types=("SHARED_IMEI",), edge_limit=2)
    checks = [
        _edge(relationship_type="RECORDED_DEVICE"),
        _edge(source_system_id="VEHICLE_REPLICA"),
        _edge(source_id=""),
        _edge(target_type="LOCATION"),
        _edge(),
    ]
    for row in checks[:-1]:
        _edge_rows(fake, [row])
        with pytest.raises(ApiError) as invalid:
            repository.list_relationship_edges(request)
        assert invalid.value.code == "CATALYST_MALFORMED_RESPONSE"
    _edge_rows(fake, [_edge(), _edge(ROWID="duplicate")])
    with pytest.raises(ApiError) as duplicate:
        repository.list_relationship_edges(request)
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"
    _edge_rows(fake, [_edge(id=f"SYN-EDGE-{index}") for index in range(3)])
    with pytest.raises(ApiError) as oversized:
        repository.list_relationship_edges(request)
    assert oversized.value.code == "CATALYST_MALFORMED_RESPONSE"
    _edge_rows(fake, [_edge(source_id="SYN-CASE-0001", target_id="SYN-CASE-0001", target_type="CASE")])
    assert repository.list_relationship_edges(request)[0]["target_id"] == "SYN-CASE-0001"


@pytest.mark.parametrize(("query", "method", "operation_request", "category", "retryable", "code"), [
    (CatalystQueryName.DISCOVERY_CANDIDATES, "list_discovery_candidates", DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",)), "timeout", True, "CATALYST_TIMEOUT"),
    (CatalystQueryName.RELATIONSHIP_EDGES, "list_relationship_edges", RelationshipPathRequest(), "unavailable", True, "CATALYST_UNAVAILABLE"),
    (CatalystQueryName.DISCOVERY_CANDIDATES, "list_discovery_candidates", DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",)), "authentication", False, "CATALYST_AUTHORIZATION_FAILED"),
])
def test_discovery_and_edge_failures_are_safe(fake, repository, query, method, operation_request, category, retryable, code):
    fake.fail(query.value, category, retryable)
    with pytest.raises(ApiError) as error:
        getattr(repository, method)(operation_request)
    assert (error.value.code, error.value.retryable) == (code, retryable)
    assert all(value not in error.value.message.lower() for value in ("http", "secret", "credential", "stack"))


def test_discovery_and_edge_sqlite_parity_for_fixed_requests(app):
    sqlite = app.extensions["repository"]
    generate(sqlite, app.config, "test")
    discovery_request = DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=10)
    edge_request = RelationshipPathRequest(source_system_ids=("CCTNS_REPLICA",), relationship_types=("SHARED_IMEI", "RECORDED_DEVICE"))
    expected_candidates = sqlite.list_discovery_candidates(discovery_request)
    expected_edges = sqlite.list_relationship_edges(edge_request)
    fake = FakeCatalystClient()
    _candidate_rows(fake, [{**row, "ROWID": f"candidate-{index}"} for index, row in enumerate(expected_candidates)])
    _edge_rows(fake, [{**row, "ROWID": f"edge-{index}"} for index, row in enumerate(expected_edges)])
    catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
    clean = lambda row: {key: value for key, value in row.items() if key != "_catalyst_rowid"}
    assert [clean(row) for row in catalyst.list_discovery_candidates(discovery_request)] == expected_candidates
    assert [clean(row) for row in catalyst.list_relationship_edges(edge_request)] == expected_edges


def test_discovery_adapter_is_unwired_and_contains_no_transport_sdk_credentials_or_raw_query_passthrough():
    adapter = Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8").lower()
    templates = Path("backend/anvaya/repositories/catalyst_templates.py").read_text(encoding="utf-8")
    for forbidden in ("import sqlite", "sqlite3", "import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "credentials_path", "os.getenv"):
        assert forbidden not in adapter
    assert "SELECT" not in Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8")
    assert "DISCOVERY_CANDIDATES" in templates and "RELATIONSHIP_EDGES" in templates
    for path in list(Path("backend/anvaya/services").glob("*.py")) + list(Path("backend/anvaya/api").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "CatalystReadOnlyRepository" not in text and "FakeCatalystClient" not in text
    with pytest.raises(ValueError):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True})
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().list_relationship_edges(RelationshipPathRequest())
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
