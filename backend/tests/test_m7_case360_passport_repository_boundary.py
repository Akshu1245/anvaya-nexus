from __future__ import annotations

from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import case_360, passport


CASE_ID = "SYN-CASE-0001"
EXTERNAL_CASE_ID = "SYN-CASE-0002"


def test_case_360_repository_returns_fixed_plain_sections_in_deterministic_order(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")

    case = repository.find_case_360_case(CASE_ID)
    assert isinstance(case, dict) and case["id"] == CASE_ID
    assert repository.find_case_360_case("SYN-CASE-MISSING") is None

    entities = repository.list_case_360_entities(CASE_ID)
    assert entities and {row["target_type"] for row in entities} >= {"PHONE", "DEVICE", "VEHICLE"}
    assert [row["edge_id"] for row in entities] == sorted(row["edge_id"] for row in entities)
    assert all(isinstance(row, dict) and not hasattr(row, "execute") for row in entities)
    assert all(row["entity_source_record_id"].startswith("SYN-SR-") for row in entities)

    evidence = repository.list_case_360_evidence(CASE_ID)
    forensics = repository.list_case_360_forensics(CASE_ID)
    issues = repository.list_case_360_trust_issues(CASE_ID)
    assert [row["id"] for row in evidence] == sorted(row["id"] for row in evidence)
    assert [row["id"] for row in forensics] == sorted(row["id"] for row in forensics)
    assert [row["id"] for row in issues] == sorted(row["id"] for row in issues)


def test_case_360_service_preserves_jurisdiction_policy_and_masking(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    investigator = repository.find_user_by_id("SYN-USR-INV")
    analyst = repository.find_user_by_id("SYN-USR-ANL")

    external = case_360(repository, investigator, "Active Case Investigation", EXTERNAL_CASE_ID)
    assert external["overview"]["masking"]["level"] == "EXTERNAL"
    analyst_view = case_360(repository, analyst, "Pattern Research", CASE_ID)
    assert analyst_view["overview"]["masking"]["level"] == "ANALYST"
    assert analyst_view["overview"]["source_record_references"]


def test_source_passport_repository_preserves_safe_provenance_and_event_order(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    source_id = repository.find_case_360_case(CASE_ID)["source_record_id"]

    record = repository.find_source_passport_record(source_id)
    assert isinstance(record, dict) and record["id"] == source_id
    assert record["source_name"] and record["version"] and record["checksum"]
    assert record["source_updated_at"] and record["imported_at"]
    assert record["access_class"] and record["reliability_role"] and record["freshness_state"]
    assert repository.find_source_passport_record("SYN-SR-MISSING") is None

    events = repository.list_source_transformations(source_id)
    assert events
    assert [(row["occurred_at"], row["operation"]) for row in events] == sorted(
        (row["occurred_at"], row["operation"]) for row in events
    )
    assert all(isinstance(row, dict) and not hasattr(row, "execute") for row in events)


def test_source_passport_omits_raw_payloads_and_reports_missing_provenance(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    analyst = repository.find_user_by_id("SYN-USR-ANL")
    source_id = repository.find_case_360_case(EXTERNAL_CASE_ID)["source_record_id"]

    result = passport(repository, analyst, "Pattern Research", source_id)
    assert result["masking_state"]["level"] == "ANALYST"
    assert "original_source_value" not in result
    assert "payload_json" not in result and "checksum" not in result
    missing = passport(repository, analyst, "Pattern Research", "SYN-SR-MISSING")
    assert missing["warning"] == "No provenance available."


def test_catalyst_case_360_and_passport_placeholders_fail_without_fallback():
    placeholder = CatalystRepositoryPlaceholder()
    operations = (
        lambda: placeholder.find_case_360_case(CASE_ID),
        lambda: placeholder.list_case_360_entities(CASE_ID),
        lambda: placeholder.list_case_360_evidence(CASE_ID),
        lambda: placeholder.list_case_360_forensics(CASE_ID),
        lambda: placeholder.list_case_360_trust_issues(CASE_ID),
        lambda: placeholder.find_source_passport_record("SYN-SR-1"),
        lambda: placeholder.list_source_transformations("SYN-SR-1"),
    )
    for operation in operations:
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_investigation_service_and_case_passport_api_orchestration_are_sql_free():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    service = (root / "services" / "investigation.py").read_text(encoding="utf-8")
    assert "repository.connection" not in service
    assert ".execute(" not in service and ".executemany(" not in service
    assert "SELECT " not in service and "INSERT " not in service and "UPDATE " not in service
    api = (root / "api" / "m3.py").read_text(encoding="utf-8")
    for name in ("case_review", "source_passport"):
        handler = api.split(f"def {name}", 1)[1].split("\n@", 1)[0]
        assert "repository.connection" not in handler
        assert ".execute(" not in handler and ".executemany(" not in handler
        assert "SELECT " not in handler and "INSERT " not in handler and "UPDATE " not in handler
    assert "find_any_entity" not in service
    assert "arbitrary_table" not in service
