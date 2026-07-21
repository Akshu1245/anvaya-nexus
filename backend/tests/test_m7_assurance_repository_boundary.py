from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.services.generator import generate
from backend.anvaya.services.intelligence import actions, assurance, challenge, dna, graph, verify


CASE_ID = "SYN-CASE-0001"
OTHER_CASE = "SYN-CASE-0002"


def test_assurance_repository_returns_fixed_plain_seeded_issues_in_order(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")

    scoped = repository.list_assurance_trust_issues(CASE_ID)
    all_issues = repository.list_assurance_trust_issues()
    assert scoped and all(issue["case_id"] == CASE_ID for issue in scoped)
    assert [issue["id"] for issue in scoped] == sorted(issue["id"] for issue in scoped)
    assert [issue["id"] for issue in all_issues] == sorted(issue["id"] for issue in all_issues)
    assert any(issue["issue_type"] == "missing_source" for issue in scoped)
    assert repository.list_assurance_trust_issues("SYN-CASE-MISSING") == []
    assert all(isinstance(issue, dict) and not hasattr(issue, "execute") for issue in all_issues)


def test_assurance_service_is_deterministic_safe_and_preserves_seeded_semantics(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")

    first = assurance(repository, CASE_ID)
    second = assurance(repository, CASE_ID)
    assert first == second
    assert first and all(item["id"].startswith("ASSURE-") for item in first)
    assert any(item["rule_id"] == "SEEDED_MISSING_SOURCE" for item in first)
    assert all(item["suggested_review_action"].startswith("Review source-backed") for item in first)
    rendered = " ".join(str(item) for item in first).lower()
    assert "guilt" not in rendered and "offender" not in rendered and "prediction" not in rendered
    assert assurance(repository, "SYN-CASE-MISSING") == []


def test_assurance_boundary_leaves_dna_graph_challenge_actions_and_verify_behaviour_available(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    assert dna(repository, user, "Active Case Investigation", CASE_ID, OTHER_CASE)["score"] <= 100
    assert graph(repository, user, "Active Case Investigation", CASE_ID)["nodes"]
    assert challenge(repository, user, "Active Case Investigation", CASE_ID, "These cases may connect")["provenance"]
    assert actions(repository, user, "Active Case Investigation", CASE_ID)["actions"]
    assert verify(repository, user, "Active Case Investigation", CASE_ID, OTHER_CASE)["automatic_merge"] is False


def test_catalyst_assurance_placeholder_fails_without_fallback():
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().list_assurance_trust_issues(CASE_ID)
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_assurance_service_and_api_handler_are_sql_free_and_intelligence_is_now_sql_free():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    service = (root / "services" / "intelligence.py").read_text(encoding="utf-8")
    assurance_segment = service.split("def assurance", 1)[1].split("\ndef ", 1)[0]
    assert "repo.connection" not in assurance_segment and "repository.connection" not in assurance_segment
    assert ".execute(" not in assurance_segment and ".executemany(" not in assurance_segment
    assert "SELECT " not in assurance_segment and "INSERT " not in assurance_segment and "UPDATE " not in assurance_segment
    assert "repo.connection" not in service and "repository.connection" not in service
    assert ".execute(" not in service and ".executemany(" not in service

    api = (root / "api" / "m3.py").read_text(encoding="utf-8")
    handler = api.split("def m5_assurance", 1)[1].split("\n@", 1)[0]
    assert "connection" not in handler and ".execute(" not in handler
    assert "fetch_entities" not in (root / "repositories" / "base.py").read_text(encoding="utf-8")
