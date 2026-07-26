from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.services import auth


def _demo_password(app):
    return app.config["DEMO_PASSWORD"]


def test_auth_repository_methods_return_plain_records_and_preserve_identity(app):
    repository = app.extensions["repository"]
    investigator = repository.find_active_user_by_username("investigator.demo")

    assert investigator == {
        "id": "SYN-USR-INV",
        "username": "investigator.demo",
        "password_hash": investigator["password_hash"],
        "role": "INVESTIGATOR",
        "assigned_station": "SYN-STN-01",
        "assigned_district": "SYN-DST-01",
        "active": 1,
    }
    assert isinstance(investigator, dict)
    assert repository.find_user_by_id(investigator["id"])["username"] == "investigator.demo"
    assert repository.find_active_user_by_username("missing.demo") is None
    assert not hasattr(investigator, "execute")


def test_auth_session_contract_create_read_revoke_and_expiry(app):
    repository = app.extensions["repository"]
    token, user = auth.login(repository, "investigator.demo", _demo_password(app), 60, "m7-auth")
    session = repository.find_session_with_user(hashlib.sha256(token.encode()).hexdigest())
    assert isinstance(session, dict)
    assert session["id"] == user["id"]
    assert auth.current_user(repository, token)["role"] == "INVESTIGATOR"

    repository.revoke_session(session["session_id"], datetime.now(timezone.utc).isoformat())
    with pytest.raises(ApiError, match="Session has been revoked"):
        auth.current_user(repository, token)

    expired_token, _ = auth.login(repository, "investigator.demo", _demo_password(app), 60, "m7-expiry")
    repository.connection.execute(
        "UPDATE sessions SET expires_at=? WHERE token_hash=?",
        (
            (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            hashlib.sha256(expired_token.encode()).hexdigest(),
        ),
    )
    repository.connection.commit()
    with pytest.raises(ApiError, match="Session has expired"):
        auth.current_user(repository, expired_token, "m7-expiry")


def test_auth_service_regression_inactive_user_and_safe_login_errors(client, app):
    repository = app.extensions["repository"]
    repository.connection.execute("UPDATE users SET active=0 WHERE username=?", ("investigator.demo",))
    repository.connection.commit()

    response = client.post("/api/auth/login", json={"username": "investigator.demo", "password": _demo_password(app)})
    assert response.status_code == 401
    assert response.json["code"] == "INVALID_CREDENTIALS"
    assert _demo_password(app) not in str(response.json)


def test_schema_health_uses_repository_contract_and_public_health_stays_unchanged(client, app, monkeypatch):
    repository = app.extensions["repository"]
    called = {"schema": 0, "health": 0}
    original_schema_version = repository.schema_version
    original_health_check = repository.health_check

    def schema_version():
        called["schema"] += 1
        return original_schema_version()

    def health_check():
        called["health"] += 1
        return original_health_check()

    monkeypatch.setattr(repository, "schema_version", schema_version)
    monkeypatch.setattr(repository, "health_check", health_check)
    public = client.get("/api/health")
    assert public.json["data"] == {"status": "ok", "service": "anvaya-api", "environment": "testing", "database": "ok", "public_demo_enabled": False, "ai_assist_enabled": False, "voice_enabled": False}
    login = client.post("/api/auth/login", json={"username": "investigator.demo", "password": _demo_password(app)})
    assert login.status_code == 200
    detailed = client.get("/api/system-health")
    assert detailed.status_code == 200
    assert detailed.json["data"]["migration_version"] == 16
    assert called == {"schema": 1, "health": 2}
    safe = str(detailed.json).lower()
    assert "sqlite:///" not in safe and "password" not in safe and "credential" not in safe


def test_catalyst_repository_auth_and_schema_contract_fails_without_fallback():
    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.schema_version(),
        lambda: placeholder.find_active_user_by_username("investigator.demo"),
        lambda: placeholder.find_user_by_id("SYN-USR-INV"),
        lambda: placeholder.create_session("SYN-SES-1", "SYN-USR-INV", "hash", "now", "later"),
        lambda: placeholder.find_session_with_user("hash"),
        lambda: placeholder.revoke_session("SYN-SES-1", "now"),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_auth_and_health_orchestration_do_not_access_sqlite_connection_directly():
    root = Path(__file__).resolve().parents[1] / "anvaya"
    auth_source = (root / "services" / "auth.py").read_text(encoding="utf-8")
    health_source = (root / "api" / "health.py").read_text(encoding="utf-8")
    m3_source = (root / "api" / "m3.py").read_text(encoding="utf-8")
    health_function = m3_source.split("def system_health():", 1)[1].split("@m3_blueprint.get('/audit-events')", 1)[0]

    for source in (auth_source, health_source, health_function):
        assert "repository.connection" not in source
        assert ".connection.execute" not in source
        assert ".executemany(" not in source
    assert "repo.schema_version()" in health_function
