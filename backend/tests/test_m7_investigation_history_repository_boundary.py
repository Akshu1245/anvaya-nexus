from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.anvaya.api.errors import ApiError
from backend.anvaya.api.m3 import _rate
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder


PASSWORD = "ANVAYA-DEMO-ONLY-2026"


def _login(client, username="investigator.demo"):
    return client.post("/api/auth/login", json={"username": username, "password": PASSWORD})


def _create(client, sources=None):
    return client.post(
        "/api/investigations",
        json={"title": "M7 boundary investigation", "purpose": "Active Case Investigation", "selected_sources": sources or ["CCTNS_REPLICA"]},
    )


def test_investigation_repository_contract_is_plain_scoped_and_deterministic(app):
    repository = app.extensions["repository"]
    base = {
        "user_id": "SYN-USR-INV", "title": "Repository investigation", "purpose": "Active Case Investigation",
        "selected_sources_json": json.dumps(["CCTNS_REPLICA"]), "assigned_station": "SYN-STN-01",
        "assigned_district": "SYN-DST-01",
    }
    repository.create_investigation({**base, "id": "SYN-INV-M7-ONE", "created_at": "2026-07-01T10:00:00+00:00", "updated_at": "2026-07-01T10:00:00+00:00"})
    repository.create_investigation({**base, "id": "SYN-INV-M7-TWO", "created_at": "2026-07-01T11:00:00+00:00", "updated_at": "2026-07-01T11:00:00+00:00"})

    found = repository.find_investigation("SYN-INV-M7-ONE")
    assert isinstance(found, dict) and found["user_id"] == "SYN-USR-INV"
    assert not hasattr(found, "execute")
    assert repository.find_investigation("SYN-INV-NOT-FOUND") is None
    assert [item["id"] for item in repository.list_investigations_for_user("SYN-USR-INV")] == ["SYN-INV-M7-TWO", "SYN-INV-M7-ONE"]
    assert [item["id"] for item in repository.list_investigations_for_user("SYN-USR-INV", 1)] == ["SYN-INV-M7-TWO"]
    assert repository.list_investigations_for_user("SYN-USR-SUP") == []


def test_source_replacement_is_authorized_atomic_and_deduplicated(client):
    _login(client)
    created = _create(client).json["data"]
    unchanged = client.patch(
        f"/api/investigations/{created['id']}/sources", json={"selected_sources": ["COURT_REPLICA"]}
    )
    assert unchanged.status_code == 403
    assert client.get(f"/api/investigations/{created['id']}").json["data"]["selected_sources"] == ["CCTNS_REPLICA"]

    updated = client.patch(
        f"/api/investigations/{created['id']}/sources",
        json={"selected_sources": ["CCTNS_REPLICA", "CCTNS_REPLICA", "VEHICLE_REPLICA"]},
    )
    assert updated.status_code == 200
    assert updated.json["data"]["selected_sources"] == ["CCTNS_REPLICA", "VEHICLE_REPLICA"]


def test_query_history_contract_is_append_only_scoped_and_preserves_snapshot(client, app):
    _login(client)
    investigation = _create(client, ["CCTNS_REPLICA", "VEHICLE_REPLICA"]).json["data"]
    preview = client.post(
        f"/api/investigations/{investigation['id']}/query/preview", json={"query": "Find SYN-FIR-000001"}
    )
    assert preview.status_code == 200
    message_id = preview.json["data"]["message_id"]
    history = client.get(f"/api/investigations/{investigation['id']}/history")
    assert history.status_code == 200 and history.json["data"][0]["id"] == message_id
    saved = app.extensions["repository"].find_investigation_message(investigation["id"], message_id)
    assert saved["request_id"] and saved["execution_intent"] == "SEARCH"
    assert json.loads(saved["query_plan_json"])["selected_sources"] == ["CCTNS_REPLICA", "VEHICLE_REPLICA"]

    client.post("/api/auth/logout")
    _rate.clear()
    _login(client, "analyst.demo")
    assert client.get(f"/api/investigations/{investigation['id']}/history").status_code == 404
    assert client.post(
        f"/api/investigations/{investigation['id']}/query/{message_id}/confirm",
        json=json.loads(saved["query_plan_json"]),
    ).status_code == 404


def test_repository_message_order_and_confirmation_are_investigation_scoped(app):
    repository = app.extensions["repository"]
    repository.create_investigation({
        "id": "SYN-INV-M7-HISTORY", "user_id": "SYN-USR-INV", "title": "History", "purpose": "Active Case Investigation",
        "selected_sources_json": "[]", "assigned_station": "SYN-STN-01", "assigned_district": "SYN-DST-01",
        "created_at": "2026-07-01T10:00:00+00:00", "updated_at": "2026-07-01T10:00:00+00:00",
    })
    for message_id, created_at in (("SYN-MSG-M7-A", "2026-07-01T10:00:00+00:00"), ("SYN-MSG-M7-B", "2026-07-01T11:00:00+00:00")):
        repository.create_investigation_message({"id": message_id, "investigation_id": "SYN-INV-M7-HISTORY", "original_text": "synthetic", "query_plan_json": "{}", "created_at": created_at})
    assert [item["id"] for item in repository.list_investigation_messages("SYN-INV-M7-HISTORY")] == ["SYN-MSG-M7-A", "SYN-MSG-M7-B"]
    assert repository.confirm_investigation_message("SYN-INV-M7-HISTORY", "SYN-MSG-M7-A", '{"intent":"SEARCH"}')
    assert not repository.confirm_investigation_message("SYN-INV-M7-OTHER", "SYN-MSG-M7-A", "{}")


def test_catalyst_investigation_and_history_methods_fail_without_fallback():
    placeholder = CatalystRepositoryPlaceholder()
    for operation in (
        lambda: placeholder.create_investigation({}), lambda: placeholder.find_investigation("SYN-INV-1"),
        lambda: placeholder.list_investigations_for_user("SYN-USR-INV"),
        lambda: placeholder.replace_investigation_sources("SYN-INV-1", "[]", "now"),
        lambda: placeholder.create_investigation_message({}),
        lambda: placeholder.find_investigation_message("SYN-INV-1", "SYN-MSG-1"),
        lambda: placeholder.list_investigation_messages("SYN-INV-1"),
        lambda: placeholder.confirm_investigation_message("SYN-INV-1", "SYN-MSG-1", "{}"),
    ):
        with pytest.raises(ApiError) as error:
            operation()
        assert error.value.code == "CATALYST_NOT_IMPLEMENTED"


def test_scoped_investigation_api_functions_have_no_direct_sql_or_connection_access():
    source = (Path(__file__).resolve().parents[1] / "anvaya" / "api" / "m3.py").read_text(encoding="utf-8")
    scoped = (
        "create_investigation", "_investigation", "_normalise_investigation", "investigations", "investigation_home",
        "investigation", "_owned", "update_sources", "apply_preset", "history", "preview", "follow_up", "confirm",
    )
    for name in scoped:
        segment = source.split(f"def {name}", 1)[1].split("\n@", 1)[0]
        assert "repository.connection" not in segment
        assert "repo.connection" not in segment
        assert ".execute(" not in segment and ".executemany(" not in segment
        assert "SELECT " not in segment and "INSERT " not in segment and "UPDATE " not in segment
