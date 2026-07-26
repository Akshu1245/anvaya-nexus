"""Offline fake-client contracts for bounded M5 intelligence storage reads."""
from __future__ import annotations

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.repositories.intelligence_requests import CaseDnaRequest, EvidenceGraphRequest
from backend.anvaya.services.generator import generate
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient

CASE = "SYN-CASE-0001"
OTHER = "SYN-CASE-0002"
SOURCE = "SYN-SR-CCTNS_REPLICA-SYN-EDGE-GOLDEN-1"


def _edge(**changes):
    row = {"ROWID": "edge-row", "id": "SYN-EDGE-01", "source_type": "CASE", "source_id": CASE, "target_type": "DEVICE", "target_id": "SYN-DEV-0001", "relationship_type": "SHARED_IMEI", "edge_class": "DIRECT_EVIDENCE", "source_record_id": SOURCE, "payload": "never"}
    row.update(changes)
    return row


def _issue(**changes):
    row = {"ROWID": "issue-row", "id": "SYN-ISSUE-01", "case_id": CASE, "issue_type": "missing_source", "severity": "SEEDED", "description": "Synthetic issue", "source_record_ids_json": "[]", "status": "OPEN", "raw": "never"}
    row.update(changes)
    return row


@pytest.fixture()
def fake(): return FakeCatalystClient()


@pytest.fixture()
def repository(fake): return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


def test_case_dna_edges_are_typed_scoped_ordered_and_safe(fake, repository):
    request = CaseDnaRequest(CASE, OTHER)
    fake.register_rows(CatalystQueryName.CASE_DNA_EDGES.value, [_edge(id="SYN-EDGE-Z"), _edge(id="SYN-EDGE-A")])
    result = repository.list_case_dna_edges(CASE, request)
    assert [row["id"] for row in result] == ["SYN-EDGE-A", "SYN-EDGE-Z"]
    assert "payload" not in result[0] and result[0]["_catalyst_rowid"] == "edge-row"
    assert fake.request_history[-1].parameters.values == {"case_id": CASE, "source_system_ids": ("CCTNS_REPLICA",)}
    with pytest.raises(ApiError) as wrong_pair: repository.list_case_dna_edges("SYN-CASE-9999", request)
    assert wrong_pair.value.code == "CATALYST_INVALID_PARAMETERS"
    fake.register_rows(CatalystQueryName.CASE_DNA_EDGES.value, [_edge(target_type="ORGANISATION")])
    with pytest.raises(ApiError) as bad_type: repository.list_case_dna_edges(CASE, request)
    assert bad_type.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.CASE_DNA_EDGES.value, [_edge(), _edge(ROWID="duplicate")])
    with pytest.raises(ApiError) as duplicate: repository.list_case_dna_edges(CASE, request)
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_evidence_graph_edges_enforce_fixed_scope_and_relationships(fake, repository):
    request = EvidenceGraphRequest(CASE, edge_limit=2)
    fake.register_rows(CatalystQueryName.EVIDENCE_GRAPH_EDGES.value, [_edge(id="SYN-EDGE-B", relationship_type="RECORDED_DEVICE"), _edge(id="SYN-EDGE-A")])
    assert [row["id"] for row in repository.list_evidence_graph_edges(request)] == ["SYN-EDGE-A", "SYN-EDGE-B"]
    fake.register_rows(CatalystQueryName.EVIDENCE_GRAPH_EDGES.value, [_edge(relationship_type="RAW")])
    with pytest.raises(ApiError) as relationship: repository.list_evidence_graph_edges(request)
    assert relationship.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.EVIDENCE_GRAPH_EDGES.value, [_edge(source_id=OTHER)])
    with pytest.raises(ApiError) as cross_case: repository.list_evidence_graph_edges(request)
    assert cross_case.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.EVIDENCE_GRAPH_EDGES.value, [_edge(id=f"SYN-EDGE-{index}") for index in range(3)])
    with pytest.raises(ApiError) as cap: repository.list_evidence_graph_edges(request)
    assert cap.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_assurance_issues_are_scoped_ordered_and_append_only_reads(fake, repository):
    fake.register_rows(CatalystQueryName.ASSURANCE_TRUST_ISSUES.value, [_issue(id="SYN-ISSUE-Z"), _issue(id="SYN-ISSUE-A")])
    all_issues = repository.list_assurance_trust_issues()
    assert [row["id"] for row in all_issues] == ["SYN-ISSUE-A", "SYN-ISSUE-Z"] and "raw" not in all_issues[0]
    fake.register_rows(CatalystQueryName.ASSURANCE_TRUST_ISSUES_BY_CASE.value, [_issue()])
    assert repository.list_assurance_trust_issues(CASE)[0]["case_id"] == CASE
    fake.register_rows(CatalystQueryName.ASSURANCE_TRUST_ISSUES_BY_CASE.value, [_issue(case_id=OTHER)])
    with pytest.raises(ApiError) as cross_case: repository.list_assurance_trust_issues(CASE)
    assert cross_case.value.code == "CATALYST_MALFORMED_RESPONSE"
    fake.register_rows(CatalystQueryName.ASSURANCE_TRUST_ISSUES.value, [])
    assert repository.list_assurance_trust_issues() == []


@pytest.mark.parametrize(("query", "method", "argument", "category", "code"), [
    (CatalystQueryName.CASE_DNA_EDGES, "list_case_dna_edges", (CASE, CaseDnaRequest(CASE, OTHER)), "timeout", "CATALYST_TIMEOUT"),
    (CatalystQueryName.EVIDENCE_GRAPH_EDGES, "list_evidence_graph_edges", (EvidenceGraphRequest(CASE),), "unavailable", "CATALYST_UNAVAILABLE"),
    (CatalystQueryName.ASSURANCE_TRUST_ISSUES, "list_assurance_trust_issues", (), "authentication", "CATALYST_AUTHORIZATION_FAILED"),
])
def test_intelligence_failures_are_translated_safely(fake, repository, query, method, argument, category, code):
    fake.fail(query.value, category, category in {"timeout", "unavailable"})
    with pytest.raises(ApiError) as error: getattr(repository, method)(*argument)
    assert error.value.code == code
    assert all(token not in error.value.message.lower() for token in ("http", "secret", "credential", "stack"))


def test_intelligence_sqlite_fake_parity(app):
    sqlite = app.extensions["repository"]; generate(sqlite, app.config, "test")
    dna_request, graph_request = CaseDnaRequest(CASE, OTHER), EvidenceGraphRequest(CASE)
    fake = FakeCatalystClient()
    for query, rows in ((CatalystQueryName.CASE_DNA_EDGES, sqlite.list_case_dna_edges(CASE, dna_request)), (CatalystQueryName.EVIDENCE_GRAPH_EDGES, sqlite.list_evidence_graph_edges(graph_request)), (CatalystQueryName.ASSURANCE_TRUST_ISSUES, sqlite.list_assurance_trust_issues()), (CatalystQueryName.ASSURANCE_TRUST_ISSUES_BY_CASE, sqlite.list_assurance_trust_issues(CASE))):
        fake.register_rows(query.value, [{**row, "ROWID": str(index)} for index, row in enumerate(rows)])
    catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
    clean = lambda rows: [{key: value for key, value in row.items() if key != "_catalyst_rowid"} for row in rows]
    assert clean(catalyst.list_case_dna_edges(CASE, dna_request)) == sqlite.list_case_dna_edges(CASE, dna_request)
    assert clean(catalyst.list_evidence_graph_edges(graph_request)) == sqlite.list_evidence_graph_edges(graph_request)
    assert clean(catalyst.list_assurance_trust_issues()) == sqlite.list_assurance_trust_issues()
    assert clean(catalyst.list_assurance_trust_issues(CASE)) == sqlite.list_assurance_trust_issues(CASE)


def test_intelligence_unsupported_writes_and_methods_remain_unavailable(repository):
    for method, arguments in (("create_session", ({},)), ("create_report_with_initial_version", ({}, {})), ("append_audit_event", (None,))):
        with pytest.raises(ApiError) as error: getattr(repository, method)(*arguments)
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
