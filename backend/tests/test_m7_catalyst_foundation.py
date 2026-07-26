import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.capabilities import Capability, CapabilityState, CapabilitySummary
from backend.anvaya.platform.factory import select_platform_adapters, validate_platform_config


def _config(**overrides):
    config = {
        "ENV_NAME": "development", "STORAGE_BACKEND": "sqlite", "AUTH_BACKEND": "prototype",
        "ARTIFACT_STORAGE": "local", "CATALYST_ENABLED": False, "CATALYST_DATASTORE_ENABLED": False,
        "CATALYST_AUTH_ENABLED": False, "CATALYST_FILE_STORAGE_ENABLED": False,
        "CATALYST_PROJECT_ID": "", "CATALYST_ENVIRONMENT": "", "CATALYST_API_BASE": "",
    }
    config.update(overrides)
    return config


def test_default_adapters_and_local_startup(app):
    adapters = app.extensions["platform_adapters"]
    assert adapters.repository.backend_name == "sqlite"
    assert adapters.authentication.backend_name == "prototype"
    assert adapters.artifact_storage.backend_name == "local"
    assert adapters.repository.health_check() == "ok"


@pytest.mark.parametrize(("field", "value"), [("STORAGE_BACKEND", "bad"), ("AUTH_BACKEND", "bad"), ("ARTIFACT_STORAGE", "bad")])
def test_invalid_backend_values_are_rejected(field, value):
    with pytest.raises(ValueError, match="Unsupported"):
        validate_platform_config(_config(**{field: value}))


def test_catalyst_requires_explicit_enablement_and_never_falls_back(app):
    with pytest.raises(ValueError, match="CATALYST_ENABLED"):
        validate_platform_config(_config(STORAGE_BACKEND="catalyst"))
    with pytest.raises(ValueError, match="injected datastore client"):
        create_app("development", {
            "STORAGE_BACKEND": "catalyst",
            "AUTH_BACKEND": "prototype",
            "ARTIFACT_STORAGE": "local",
            "CATALYST_ENABLED": True,
            "CATALYST_DATASTORE_ENABLED": True,
            "CATALYST_AUTH_ENABLED": False,
            "CATALYST_FILE_STORAGE_ENABLED": False,
            "CATALYST_PROJECT_ID": "synthetic-development-project",
            "CATALYST_ENVIRONMENT": "Development",
            "CATALYST_API_BASE": "https://example.invalid",
            "CATALYST_DATASTORE_CLIENT": None,
        })

def test_catalyst_production_requires_safe_placeholder_configuration():
    with pytest.raises(ValueError, match="requires project"):
        validate_platform_config(_config(ENV_NAME="production", STORAGE_BACKEND="catalyst", CATALYST_ENABLED=True))
    validate_platform_config(_config(ENV_NAME="production", STORAGE_BACKEND="catalyst", CATALYST_ENABLED=True, CATALYST_PROJECT_ID="placeholder", CATALYST_ENVIRONMENT="development", CATALYST_API_BASE="https://placeholder.invalid"))


def test_capability_states_are_safe_and_complete(client, app):
    summary = CapabilitySummary(tuple(Capability("test", state, "safe") for state in CapabilityState)).safe_dict()
    assert {item["state"] for item in summary["capabilities"]} == {state.value for state in CapabilityState}
    assert "PROJECT" not in str(summary) and "CREDENTIAL" not in str(summary)
    public = client.get("/api/health").json["data"]
    assert set(public).issuperset({"status", "service", "environment", "database", "public_demo_enabled", "ai_assist_enabled", "voice_enabled"})
    login = client.post("/api/auth/login", json={"username": "investigator.demo", "password": "ANVAYA-DEMO-ONLY-2026"})
    assert login.status_code == 200
    detailed = client.get("/api/system-health").json["data"]
    capabilities = detailed["platform_capabilities"]["capabilities"]
    assert {item["name"] for item in capabilities} == {"persistence_transactions", "authentication", "artifact_storage", "schema_bootstrap", "synthetic_seed", "health_integration", "catalyst_client_foundation", "catalyst_readonly_contract", "catalyst_live_transport", "catalyst_production_repository", "catalyst_write_repository", "catalyst_schema_bootstrap"}
    assert "credentials_path" not in str(detailed).lower()


def test_local_artifact_and_prototype_session_wrappers_remain_operational(app):
    adapters = app.extensions["platform_adapters"]
    token, user = adapters.authentication.login_session("investigator.demo", "ANVAYA-DEMO-ONLY-2026", 60, "m7-test")
    assert adapters.authentication.resolve_identity(token, "m7-test")["id"] == user["id"]
    adapters.artifact_storage.store_report_html("safe-report", "<p>synthetic</p>")
    assert adapters.artifact_storage.retrieve_artifact("safe-report") == "<p>synthetic</p>"
    adapters.authentication.revoke_session(token, "m7-test")
