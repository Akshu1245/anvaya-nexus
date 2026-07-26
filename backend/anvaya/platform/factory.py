from __future__ import annotations

from dataclasses import dataclass

from backend.anvaya.platform.adapters import (
    CatalystArtifactStoragePlaceholder, CatalystAuthenticationPlaceholder,
    CatalystSchemaBootstrapPlaceholder, LocalArtifactStorageAdapter, LocalSchemaBootstrapAdapter,
    PrototypeAuthenticationAdapter, SQLiteRepositoryAdapter,
)
from backend.anvaya.platform.capabilities import Capability, CapabilityState, CapabilitySummary


@dataclass(frozen=True)
class PlatformAdapters:
    repository: object
    authentication: object
    artifact_storage: object
    schema_bootstrap: object


def validate_platform_config(config) -> None:
    values = {
        "STORAGE_BACKEND": (config["STORAGE_BACKEND"], {"sqlite", "catalyst"}),
        "AUTH_BACKEND": (config["AUTH_BACKEND"], {"prototype", "catalyst"}),
        "ARTIFACT_STORAGE": (config["ARTIFACT_STORAGE"], {"local", "catalyst"}),
    }
    for name, (value, allowed) in values.items():
        if value not in allowed:
            raise ValueError(f"Unsupported {name}: {value}")
    selected_catalyst = any(value == "catalyst" for value, _ in values.values())
    enabled_flags = any(bool(config[name]) for name in ("CATALYST_DATASTORE_ENABLED", "CATALYST_AUTH_ENABLED", "CATALYST_FILE_STORAGE_ENABLED"))
    if (selected_catalyst or enabled_flags) and not config["CATALYST_ENABLED"]:
        raise ValueError("Catalyst components require ANVAYA_CATALYST_ENABLED=true")
    if config["ENV_NAME"] == "production" and selected_catalyst:
        required = ("CATALYST_PROJECT_ID", "CATALYST_ENVIRONMENT", "CATALYST_API_BASE")
        if any(not str(config.get(name, "")).strip() for name in required):
            raise ValueError("Catalyst production mode requires project, environment, and API base configuration")


def select_platform_adapters(config, repository) -> PlatformAdapters:
    validate_platform_config(config)
    selected = {
        "repository": repository if config["STORAGE_BACKEND"] == "catalyst" else SQLiteRepositoryAdapter(repository),
        "authentication": CatalystAuthenticationPlaceholder() if config["AUTH_BACKEND"] == "catalyst" else PrototypeAuthenticationAdapter(repository),
        "artifact_storage": CatalystArtifactStoragePlaceholder() if config["ARTIFACT_STORAGE"] == "catalyst" else LocalArtifactStorageAdapter(),
        "schema_bootstrap": CatalystSchemaBootstrapPlaceholder() if config["CATALYST_ENABLED"] else LocalSchemaBootstrapAdapter(repository),
    }
    return PlatformAdapters(**selected)


def capability_summary(config, adapters: PlatformAdapters) -> CapabilitySummary:
    catalyst_client_state = CapabilityState.CONFIGURED if config["CATALYST_ENABLED"] else CapabilityState.DISABLED
    live_read_state = CapabilityState.CONFIGURED if config["STORAGE_BACKEND"] == "catalyst" else CapabilityState.DISABLED
    entries = [
        adapters.repository.transaction_capability(),
        adapters.authentication.capability(),
        adapters.artifact_storage.capability(),
        adapters.schema_bootstrap.capability(),
        Capability("synthetic_seed", CapabilityState.AVAILABLE if config["STORAGE_BACKEND"] == "sqlite" else CapabilityState.DEGRADED, "Synthetic local seed remains available only for SQLite."),
        Capability("health_integration", CapabilityState.CONFIGURED if config["STORAGE_BACKEND"] == "catalyst" else CapabilityState.AVAILABLE, "Catalyst health performs one bounded provider read when read-only mode is selected."),
        Capability("catalyst_client_foundation", catalyst_client_state, "A trusted bootstrap layer or AppSail request context supplies the provider datastore client."),
        Capability("catalyst_readonly_contract", CapabilityState.AVAILABLE, "Fixed server-owned read templates are application-wired without a SQLite fallback."),
        Capability("catalyst_live_transport", live_read_state, "AppSail mode initializes the official Python SDK per request; only the validated source-system read slice is enabled."),
        Capability("catalyst_production_repository", CapabilityState.UNAVAILABLE, "Production Catalyst mode remains prohibited."),
        Capability("catalyst_write_repository", CapabilityState.UNAVAILABLE, "Catalyst writes, sessions, imports, and seeding remain unavailable."),
        Capability("catalyst_schema_bootstrap", CapabilityState.UNAVAILABLE, "Catalyst schema verification and bootstrap remain unavailable."),
    ]
    return CapabilitySummary(tuple(entries))
