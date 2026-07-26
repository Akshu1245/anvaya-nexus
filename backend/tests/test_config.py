import shutil
import tempfile
from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.config import DevelopmentConfig, ProductionConfig, TestingConfig, config_for, validate_catalyst_readonly_config, validate_production_config


@pytest.mark.parametrize(("name", "expected"), [("development", DevelopmentConfig), ("testing", TestingConfig), ("production", ProductionConfig)])
def test_named_configurations(name, expected):
    assert config_for(name) is expected


def test_unknown_configuration_is_rejected():
    with pytest.raises(ValueError, match="Unsupported ANVAYA_ENV"):
        config_for("unknown")


def test_testing_configuration_uses_memory_sqlite():
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["DATABASE_URL"] == "sqlite:///:memory:"
    app.extensions["repository"].close()


def test_production_validation_fails_closed_for_missing_secret_and_bad_origin():
    with pytest.raises(ValueError, match="SESSION_SECRET"):
        validate_production_config({"SESSION_SECRET": "", "ALLOWED_ORIGINS": "https://anvaya.example.test", "MAX_CONTENT_LENGTH": 1, "MAX_UPLOAD_BYTES": 1})
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        validate_production_config({"SESSION_SECRET": "x" * 32, "ALLOWED_ORIGINS": "http://unsafe.example.test", "MAX_CONTENT_LENGTH": 1, "MAX_UPLOAD_BYTES": 1})


def test_public_demo_production_requires_private_server_side_password():
    base = {"SESSION_SECRET": "x" * 32, "ALLOWED_ORIGINS": "https://anvaya.example.test", "MAX_CONTENT_LENGTH": 1, "MAX_UPLOAD_BYTES": 1, "PUBLIC_DEMO_MODE": True}
    with pytest.raises(ValueError, match="DEMO_PASSWORD"):
        validate_production_config({**base, "DEMO_PASSWORD": ""})
    validate_production_config({**base, "DEMO_PASSWORD": "d" * 24})


def test_local_sqlite_and_partial_catalyst_configuration_do_not_silently_fallback():
    validate_catalyst_readonly_config({"STORAGE_BACKEND": "sqlite"})
    with pytest.raises(ValueError, match="CATALYST_ENABLED"):
        validate_catalyst_readonly_config({"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": False, "CATALYST_DATASTORE_ENABLED": False})


def test_catalyst_readonly_is_development_only_even_with_an_injected_client():
    class Client:
        def execute_read(self): ...
        def health_check(self): ...
        def close(self): ...

    base = {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True, "CATALYST_DATASTORE_ENABLED": True, "CATALYST_ENVIRONMENT": "Development", "CATALYST_RUNTIME": "appsail", "CATALYST_PROJECT_ID": "synthetic-project", "CATALYST_API_BASE": "sdk-request-context", "CATALYST_DATASTORE_CLIENT": Client()}
    validate_catalyst_readonly_config({**base, "ENV_NAME": "development"})
    with pytest.raises(ValueError, match="not authorized for production"):
        validate_catalyst_readonly_config({**base, "ENV_NAME": "production"})


def test_migrations_are_safe_on_repeated_startup():
    tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    try:
        database = f"sqlite:///{Path(tmpdir.name) / 'repeatable.db'}"
        first = create_app("development", {"DATABASE_URL": database})
        first.extensions["repository"].close()
        second = create_app("development", {"DATABASE_URL": database})
        assert second.extensions["repository"].connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 16
        second.extensions["repository"].close()
    finally:
        shutil.rmtree(tmpdir.name, ignore_errors=True)
