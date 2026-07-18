import pytest

from backend.anvaya import create_app
from backend.anvaya.config import DevelopmentConfig, ProductionConfig, TestingConfig, config_for, validate_production_config


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


def test_migrations_are_safe_on_repeated_startup(tmp_path):
    database = f"sqlite:///{tmp_path / 'repeatable.db'}"
    first = create_app("development", {"DATABASE_URL": database})
    first.extensions["repository"].close()
    second = create_app("development", {"DATABASE_URL": database})
    assert second.extensions["repository"].connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 6
    second.extensions["repository"].close()
