from __future__ import annotations

from backend.anvaya import create_app
from backend.anvaya.platform.catalyst_sdk_client import CatalystSdkDataStoreClient


class FakeZCQL:
    def __init__(self):
        self.queries = []

    def execute_query(self, query):
        self.queries.append(query)
        return []


class FakeCatalystApp:
    def __init__(self):
        self.service = FakeZCQL()

    def zcql(self):
        return self.service


def appsail_config(initializer):
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
        "CATALYST_RUNTIME": "appsail",
        "CATALYST_DATASTORE_CLIENT": None,
        "CATALYST_SDK_INITIALIZER": initializer,
    }


def test_appsail_runtime_initializes_sdk_from_each_request_and_injects_client():
    calls = []
    catalyst_app = FakeCatalystApp()

    def initializer(*, req):
        calls.append(req.path)
        return catalyst_app

    app = create_app("testing", appsail_config(initializer))
    assert isinstance(app.config["CATALYST_DATASTORE_CLIENT"], CatalystSdkDataStoreClient)
    response = app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["data"]["database"] == "ok"
    assert calls == ["/api/health"]
    assert catalyst_app.service.queries == ["SELECT id FROM source_systems LIMIT 0,1"]


def test_appsail_runtime_remains_development_only():
    def initializer(*, req):
        return FakeCatalystApp()

    config = appsail_config(initializer)
    config.update({"SESSION_SECRET": "x" * 32, "ALLOWED_ORIGINS": "https://example.invalid"})
    try:
        create_app("production", config)
    except ValueError as error:
        assert "not authorized for production" in str(error)
    else:
        raise AssertionError("Production Catalyst AppSail runtime must fail closed")
