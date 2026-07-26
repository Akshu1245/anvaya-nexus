from __future__ import annotations

import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.anvaya.repositories.sqlite import SQLiteRepository


class FakeCatalystClient:
    def __init__(self):
        self.reads = []
        self.closed = False

    def execute_read(self, request):
        self.reads.append(request.query.name)
        if request.query.name == CatalystQueryName.SOURCE_SYSTEM_LIST:
            return {"status": "success", "data": []}
        return {"status": "success", "data": []}

    def health_check(self):
        return {"status": "offline_ok"}

    def close(self):
        self.closed = True


def catalyst_config(client):
    return {
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
        "CATALYST_DATASTORE_CLIENT": client,
    }


def test_sqlite_remains_default():
    app = create_app("testing")
    assert app.config["STORAGE_BACKEND"] == "sqlite"
    assert isinstance(app.extensions["repository"], SQLiteRepository)


def test_explicit_catalyst_mode_wires_readonly_repository_without_sqlite_fallback():
    client = FakeCatalystClient()
    app = create_app("testing", catalyst_config(client))
    repository = app.extensions["repository"]
    assert isinstance(repository, CatalystReadOnlyRepository)
    assert repository.backend_name == "catalyst-readonly-offline"
    assert repository.list_source_systems() == []
    assert client.reads == [CatalystQueryName.SOURCE_SYSTEM_LIST]
    with pytest.raises(ApiError) as error:
        repository.create_session("id", "user", "hash", "now", "later")
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_catalyst_health_uses_injected_client():
    client = FakeCatalystClient()
    app = create_app("testing", catalyst_config(client))
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["data"]["database"] == "ok"


def test_catalyst_mode_fails_closed_without_injected_client():
    config = catalyst_config(None)
    with pytest.raises(ValueError, match="injected datastore client"):
        create_app("testing", config)


def test_catalyst_mode_rejects_production_and_non_development_provider_environment():
    client = FakeCatalystClient()
    with pytest.raises(ValueError, match="not authorized for production"):
        create_app("production", {**catalyst_config(client), "SESSION_SECRET": "x" * 32, "ALLOWED_ORIGINS": "https://example.invalid"})
    with pytest.raises(ValueError, match="explicit non-production environment"):
        create_app("testing", {**catalyst_config(client), "CATALYST_ENVIRONMENT": "Production"})


def test_catalyst_auth_selection_remains_unavailable():
    client = FakeCatalystClient()
    with pytest.raises(ValueError, match="authentication is not implemented"):
        create_app("testing", {**catalyst_config(client), "AUTH_BACKEND": "catalyst", "CATALYST_AUTH_ENABLED": True})
