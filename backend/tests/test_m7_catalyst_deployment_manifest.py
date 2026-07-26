import json
from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName


ROOT = Path(__file__).resolve().parents[2]


def test_offline_datastore_and_query_manifests_are_complete_and_bounded():
    datastore = json.loads((ROOT / "deploy/catalyst/datastore-manifest.json").read_text())
    queries = json.loads((ROOT / "deploy/catalyst/query-template-manifest.json").read_text())
    names = [entry["table"] for entry in datastore["tables"]]
    assert datastore["mode"] == "OFFLINE_PREPARATION_ONLY"
    assert len(names) == len(set(names)) and len(names) >= 40
    assert set(datastore["seed_order"]).issubset(names)
    assert {"cases", "case_person_roles", "legal_sections", "arrest_surrender_events", "reports", "audit_events"}.issubset(names)
    template_ids = [entry["id"] for entry in queries["templates"]]
    assert set(template_ids) == {item.value for item in CatalystQueryName}
    assert len(template_ids) == len(set(template_ids))
    assert all(entry["max_rows"] > 0 for entry in queries["templates"])
    assert {entry["status"] for entry in queries["templates"]} <= {"OFFLINE_TESTED", "LIVE_VALIDATION_REQUIRED", "NOT_IMPLEMENTED"}


def test_offline_environment_privacy_and_readiness_documents_are_safe():
    env = (ROOT / "deploy/catalyst/env.example").read_text()
    privacy = (ROOT / "deploy/catalyst/privacy-manifest.md").read_text().lower()
    required = [
        ROOT / "docs/CATALYST_CUSTOM_RUNTIME_DEPLOYMENT.md",
        ROOT / "docs/OWNER_FINAL_ACTIONS.md",
        ROOT / "docs/m7-catalyst-deployment-topology.md",
        ROOT / "docs/m7-catalyst-rollback-plan.md",
        ROOT / "docs/m7-catalyst-live-validation-checklist.md",
        ROOT / "docs/submission-readiness-checklist.md",
        ROOT / "deploy/catalyst/smoke-test-plan.md",
    ]
    assert "ANVAYA_STORAGE_BACKEND=sqlite" in env
    assert "ANVAYA_AUTH_BACKEND=prototype" in env
    assert "ANVAYA_CATALYST_ENABLED=false" in env
    assert "ANVAYA_PUBLIC_DEMO_MODE=true" in env
    assert "ANVAYA-DEMO-ONLY-2026" not in env
    assert all(item.exists() for item in required)
    assert all(term in privacy for term in ("phone", "imei", "raw source payload", "demo passwords"))


def test_explicit_catalyst_mode_remains_fail_closed_and_unwired():
    with pytest.raises(ValueError, match="Catalyst components require"):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": False})
