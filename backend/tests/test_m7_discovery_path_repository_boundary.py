from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RelationshipPathRequest
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import discover, relationship_path
from backend.anvaya.services.query_parser import parse_query


def test_discovery_repository_returns_source_backed_shared_device_phone_and_vehicle_candidates(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    rows = repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",)))
    related = [row for row in rows if row["id"] == "SYN-CASE-0002"]
    assert related
    assert {row["target_type"] for row in related} >= {"DEVICE", "PHONE", "VEHICLE"}
    assert {row["relationship_type"] for row in related} >= {"SHARED_IMEI", "RECORDED_PHONE", "RECORDED_VEHICLE"}
    assert all(isinstance(row, dict) and not hasattr(row, "execute") for row in rows)
    assert all(row["source_record_id"].startswith("SYN-SR-") and row["edge_source_record_id"].startswith("SYN-SR-") for row in related)
    assert repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("VEHICLE_REPLICA",))) == []


def test_discovery_request_is_bounded_deterministic_and_rejects_unsafe_fields(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    first = repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=2))
    assert len(first) <= 2
    assert [row["incident_at"] for row in first] == sorted((row["incident_at"] for row in first), reverse=True)
    assert repository.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=1, offset=1))
    with pytest.raises(ValueError):
        DiscoveryRequest((), ("CCTNS_REPLICA",))
    with pytest.raises(ValueError):
        DiscoveryRequest(("SYN-CASE-0001",), ())
    with pytest.raises(ValueError):
        DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), limit=26)
    with pytest.raises(TypeError):
        DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",), order="sql")


def test_relationship_edges_and_paths_are_bounded_source_backed_and_allowlisted(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    request = RelationshipPathRequest(max_depth=3)
    edges = repository.list_relationship_edges(request)
    assert edges and all(edge["relationship_type"] in request.relationship_types for edge in edges)
    assert all(edge["source_record_id"].startswith("SYN-SR-") and edge["source_system_id"] == "CCTNS_REPLICA" for edge in edges)
    assert repository.list_relationship_edges(RelationshipPathRequest(source_system_ids=("VEHICLE_REPLICA",))) == []
    user = repository.find_user_by_id("SYN-USR-INV")
    two_hop = relationship_path(repository, user, "Active Case Investigation", "SYN-CASE-0001", "SYN-CASE-0002", 3)
    assert two_hop["path"] and len(two_hop["path"]) <= 3
    assert all(edge["source_record_reference"].startswith("SYN-SR-") for edge in two_hop["path"])
    one_hop = relationship_path(repository, user, "Active Case Investigation", "SYN-CASE-0001", "SYN-CASE-0002", 1)
    assert one_hop["limited"]
    no_path = relationship_path(repository, user, "Active Case Investigation", "SYN-CASE-MISSING", "SYN-CASE-0002", 3)
    assert no_path["limited"] and no_path["path"] == []
    with pytest.raises(ValueError):
        RelationshipPathRequest(max_depth=4)
    with pytest.raises(ValueError):
        RelationshipPathRequest(relationship_types=("raw-expression",))


def test_discover_service_preserves_external_masking_and_candidate_only_result(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    plan = parse_query("Find SYN-FIR-000001", ["CCTNS_REPLICA"])
    plan.intent = "DISCOVER"
    results = discover(repository, user, "Active Case Investigation", plan)
    external = next(result for result in results if result["id"] == "SYN-CASE-0002")
    assert external["candidate_relationship"] and external["masking"]["level"] == "EXTERNAL"


def test_catalyst_discovery_and_path_placeholders_fail_without_fallback():
    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.list_discovery_candidates(DiscoveryRequest(("SYN-CASE-0001",), ("CCTNS_REPLICA",))),
        lambda: placeholder.list_relationship_edges(RelationshipPathRequest()),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_discover_and_path_functions_have_no_direct_sql_or_connection_access():
    source = (Path(__file__).resolve().parents[1] / "anvaya" / "services" / "investigation.py").read_text(encoding="utf-8")
    for name in ("discover", "relationship_path"):
        segment = source.split(f"def {name}", 1)[1].split("\ndef ", 1)[0]
        assert "repository.connection" not in segment
        assert ".execute(" not in segment and ".executemany(" not in segment
        assert "SELECT " not in segment and "INSERT " not in segment and "UPDATE " not in segment
