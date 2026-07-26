from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.intelligence_requests import CaseDnaRequest, EvidenceGraphRequest
from backend.anvaya.services.generator import generate
from backend.anvaya.services.intelligence import dna, graph


LEFT = "SYN-CASE-0001"
RIGHT = "SYN-CASE-0002"


def test_case_dna_repository_returns_fixed_plain_source_scoped_similarity_inputs(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    request = CaseDnaRequest(LEFT, RIGHT, ("CCTNS_REPLICA", "CCTNS_REPLICA"))
    assert request.source_system_ids == ("CCTNS_REPLICA",)

    left = repository.find_case_dna_case(LEFT)
    right = repository.find_case_dna_case(RIGHT)
    assert isinstance(left, dict) and isinstance(right, dict)
    assert left["offence"] == right["offence"] == "CHAIN_SNATCHING"
    assert left["station_id"] and right["district_id"] and left["incident_at"]
    assert repository.find_case_dna_case("SYN-CASE-MISSING") is None

    edges = repository.list_case_dna_edges(LEFT, request)
    assert edges and [edge["id"] for edge in edges] == sorted(edge["id"] for edge in edges)
    assert {edge["target_type"] for edge in edges} >= {"PHONE", "DEVICE", "VEHICLE"}
    assert all(isinstance(edge, dict) and not hasattr(edge, "execute") for edge in edges)
    assert repository.list_case_dna_edges(LEFT, CaseDnaRequest(LEFT, RIGHT, ("VEHICLE_REPLICA",))) == []


def test_case_dna_service_is_deterministic_masked_and_similarity_only(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    investigator = repository.find_user_by_id("SYN-USR-INV")
    analyst = repository.find_user_by_id("SYN-USR-ANL")

    first = dna(repository, investigator, "Active Case Investigation", LEFT, RIGHT)
    second = dna(repository, investigator, "Active Case Investigation", LEFT, RIGHT)
    assert first == second and first["masking"] == "EXTERNAL"
    assert any(item["factor"] == "hard_device" for item in first["factors"])
    assert any(item["factor"] == "vehicle_conflict" and item["contribution"] < 0 for item in first["factors"])
    assert "ranking aid" in first["limitations"][0].lower()
    assert all(word not in " ".join(item["explanation"] for item in first["factors"]).lower() for word in ("offender", "suspect", "arrest", "risk"))
    analyst_view = dna(repository, analyst, "Pattern Research", LEFT, RIGHT)
    assert analyst_view["masking"] == "ANALYST"


def test_evidence_graph_repository_is_bounded_ordered_and_source_scoped(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    request = EvidenceGraphRequest(LEFT, source_system_ids=("CCTNS_REPLICA", "CCTNS_REPLICA"), edge_limit=20)
    assert request.source_system_ids == ("CCTNS_REPLICA",)
    root = repository.find_evidence_graph_case(request)
    edges = repository.list_evidence_graph_edges(request)
    assert root and root["id"] == LEFT
    assert edges and len(edges) <= 20
    assert [edge["id"] for edge in edges] == sorted(edge["id"] for edge in edges)
    assert all(edge["source_record_id"].startswith("SYN-SR-") for edge in edges)
    assert all(isinstance(edge, dict) and not hasattr(edge, "execute") for edge in edges)
    assert repository.list_evidence_graph_edges(EvidenceGraphRequest(LEFT, source_system_ids=("VEHICLE_REPLICA",))) == []
    assert repository.find_evidence_graph_case(EvidenceGraphRequest("SYN-CASE-MISSING")) is None


def test_evidence_graph_service_preserves_bounded_source_backed_masking(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    investigator = repository.find_user_by_id("SYN-USR-INV")
    analyst = repository.find_user_by_id("SYN-USR-ANL")

    result = graph(repository, investigator, "Active Case Investigation", LEFT)
    assert result["limits"] == {"nodes": 20, "edges": 20}
    assert result["nodes"][0] == {"id": LEFT, "type": "CASE", "masked": False}
    assert all(edge["from"] == LEFT and edge["source_record_reference"].startswith("SYN-SR-") for edge in result["edges"])
    assert all(edge["relationship_type"] in {"RECORDED_DEVICE", "SHARED_IMEI", "RECORDED_PHONE", "RECORDED_VEHICLE"} for edge in result["edges"])
    assert all(edge["to"] in {node["id"] for node in result["nodes"]} for edge in result["edges"])
    analyst_graph = graph(repository, analyst, "Pattern Research", LEFT)
    assert all(node["masked"] for node in analyst_graph["nodes"][1:])
    with pytest.raises(ApiError) as error:
        graph(repository, investigator, "Active Case Investigation", "SYN-CASE-MISSING")
    assert error.value.code == "CASE_NOT_FOUND"


def test_intelligence_requests_are_fixed_and_catalyst_methods_do_not_fallback():
    with pytest.raises(ValueError):
        CaseDnaRequest("", RIGHT)
    with pytest.raises(ValueError):
        EvidenceGraphRequest(LEFT, relationship_types=("raw-expression",))
    with pytest.raises(ValueError):
        EvidenceGraphRequest(LEFT, edge_limit=21)
    with pytest.raises(TypeError):
        EvidenceGraphRequest(LEFT, order="raw SQL")
    with pytest.raises(TypeError):
        CaseDnaRequest(LEFT, RIGHT, weights={"hard_device": 100})

    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.find_case_dna_case(LEFT),
        lambda: placeholder.list_case_dna_edges(LEFT, CaseDnaRequest(LEFT, RIGHT)),
        lambda: placeholder.find_evidence_graph_case(EvidenceGraphRequest(LEFT)),
        lambda: placeholder.list_evidence_graph_edges(EvidenceGraphRequest(LEFT)),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_case_dna_graph_functions_and_handlers_are_sql_free():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    service = (root / "services" / "intelligence.py").read_text(encoding="utf-8")
    for name in ("dna", "graph"):
        segment = service.split(f"def {name}", 1)[1].split("\ndef ", 1)[0]
        assert "repository.connection" not in segment and "repo.connection" not in segment
        assert ".execute(" not in segment and ".executemany(" not in segment
        assert "SELECT " not in segment and "INSERT " not in segment and "UPDATE " not in segment
    assert "repo.connection" not in service  # Record Assurance is boundary-clean in M7.2A-4B1.

    api = (root / "api" / "m3.py").read_text(encoding="utf-8")
    for name in ("m5_dna", "m5_graph"):
        handler = api.split(f"def {name}", 1)[1].split("\n@", 1)[0]
        assert "connection" not in handler and ".execute(" not in handler
