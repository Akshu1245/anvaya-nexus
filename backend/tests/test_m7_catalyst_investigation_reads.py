"""Offline fake-client contract checks for investigation and history reads."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.anvaya import create_app
from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.adapters import CatalystRepositoryPlaceholder
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient


def _investigation(**overrides):
    record = {
        "ROWID": "row-investigation", "id": "SYN-INV-READ-001", "user_id": "SYN-USR-INV",
        "title": "Synthetic read investigation", "purpose": "Active Case Investigation",
        "selected_sources_json": json.dumps(["CCTNS_REPLICA", "VEHICLE_REPLICA"]),
        "assigned_station": None, "assigned_district": None,
        "created_at": "2026-07-01T10:00:00+00:00", "updated_at": "2026-07-01T11:00:00+00:00",
    }
    record.update(overrides)
    return record


def _message(**overrides):
    record = {
        "ROWID": "row-message", "id": "SYN-MSG-READ-001", "original_text": "Find SYN-FIR-000001",
        "query_plan_json": json.dumps({"intent": "SEARCH", "selected_sources": ["CCTNS_REPLICA"]}),
        "confirmed": "false", "parent_message_id": None, "execution_intent": "SEARCH",
        "result_count": None, "request_id": "req-synthetic", "created_at": "2026-07-01T10:10:00+00:00",
    }
    record.update(overrides)
    return record


@pytest.fixture()
def fake():
    return FakeCatalystClient()


@pytest.fixture()
def repository(fake):
    return CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)


def _rows(fake, query, rows):
    fake.register_rows(query.value, rows)


def test_exact_investigation_read_preserves_current_contract_and_isolates_row_id(fake, repository):
    _rows(fake, CatalystQueryName.INVESTIGATION_BY_ID, [_investigation()])
    result = repository.find_investigation("SYN-INV-READ-001")
    assert result == {
        "id": "SYN-INV-READ-001", "user_id": "SYN-USR-INV", "title": "Synthetic read investigation",
        "purpose": "Active Case Investigation", "selected_sources_json": '["CCTNS_REPLICA", "VEHICLE_REPLICA"]',
        "assigned_station": None, "assigned_district": None,
        "created_at": "2026-07-01T10:00:00+00:00", "updated_at": "2026-07-01T11:00:00+00:00",
        "_catalyst_rowid": "row-investigation",
    }
    assert fake.request_history[0].query.name is CatalystQueryName.INVESTIGATION_BY_ID
    assert fake.request_history[0].parameters.values == {"id": "SYN-INV-READ-001"}


def test_investigation_missing_duplicate_and_bad_snapshot_fail_safely(fake, repository):
    _rows(fake, CatalystQueryName.INVESTIGATION_BY_ID, [])
    assert repository.find_investigation("SYN-INV-READ-001") is None
    _rows(fake, CatalystQueryName.INVESTIGATION_BY_ID, [_investigation(), _investigation(ROWID="other")])
    with pytest.raises(ApiError) as duplicate:
        repository.find_investigation("SYN-INV-READ-001")
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"
    for invalid in ("{", json.dumps({"source": "CCTNS_REPLICA"}), json.dumps(["CCTNS_REPLICA", "CCTNS_REPLICA"]), json.dumps(["bad id"]), json.dumps([None])):
        _rows(fake, CatalystQueryName.INVESTIGATION_BY_ID, [_investigation(selected_sources_json=invalid)])
        with pytest.raises(ApiError) as malformed:
            repository.find_investigation("SYN-INV-READ-001")
        assert malformed.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_owner_scoped_investigation_list_uses_fixed_order_and_cap(fake, repository):
    _rows(fake, CatalystQueryName.INVESTIGATIONS_BY_OWNER, [
        _investigation(id="SYN-INV-READ-B", updated_at="2026-07-01T11:00:00+00:00"),
        _investigation(id="SYN-INV-READ-A", updated_at="2026-07-01T11:00:00+00:00"),
    ])
    result = repository.list_investigations_for_user("SYN-USR-INV")
    assert [row["id"] for row in result] == ["SYN-INV-READ-A", "SYN-INV-READ-B"]
    assert fake.request_history[-1].parameters.values == {"user_id": "SYN-USR-INV", "limit": 50}
    assert repository.list_investigations_for_user("SYN-USR-INV", 999) == result
    assert fake.request_history[-1].parameters.values["limit"] == 50
    _rows(fake, CatalystQueryName.INVESTIGATIONS_BY_OWNER, [])
    assert repository.list_investigations_for_user("SYN-USR-OTHER") == []
    _rows(fake, CatalystQueryName.INVESTIGATIONS_BY_OWNER, [_investigation(user_id="SYN-USR-OTHER")])
    with pytest.raises(ApiError) as cross_owner:
        repository.list_investigations_for_user("SYN-USR-INV")
    assert cross_owner.value.code == "CATALYST_MALFORMED_RESPONSE"
    _rows(fake, CatalystQueryName.INVESTIGATIONS_BY_OWNER, [_investigation(id=f"SYN-INV-READ-{index:03d}") for index in range(51)])
    with pytest.raises(ApiError) as oversized:
        repository.list_investigations_for_user("SYN-USR-INV")
    assert oversized.value.code == "CATALYST_MALFORMED_RESPONSE"


def test_exact_and_scoped_query_history_reads_preserve_current_shape(fake, repository):
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_ID, [_message(confirmed="true")])
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_INVESTIGATION, [
        _message(id="SYN-MSG-READ-001", created_at="2026-07-01T10:10:00+00:00"),
        _message(id="SYN-MSG-READ-002", created_at="2026-07-01T10:11:00+00:00", parent_message_id="SYN-MSG-READ-001"),
    ])
    exact = repository.find_investigation_message("SYN-INV-READ-001", "SYN-MSG-READ-001")
    assert exact["confirmed"] is True and exact["request_id"] == "req-synthetic"
    assert exact["query_plan_json"] == _message()["query_plan_json"]
    listed = repository.list_investigation_messages("SYN-INV-READ-001")
    assert [item["id"] for item in listed] == ["SYN-MSG-READ-001", "SYN-MSG-READ-002"]
    assert listed[1]["parent_message_id"] == "SYN-MSG-READ-001" and listed[0]["_catalyst_rowid"] == "row-message"
    assert fake.request_history[0].parameters.values == {"id": "SYN-MSG-READ-001", "investigation_id": "SYN-INV-READ-001"}
    assert fake.request_history[1].parameters.values == {"investigation_id": "SYN-INV-READ-001", "limit": 50}


def test_query_history_missing_duplicate_and_malformed_data_fail_safely(fake, repository):
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_ID, [])
    assert repository.find_investigation_message("SYN-INV-READ-001", "SYN-MSG-READ-001") is None
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_ID, [_message(), _message(ROWID="other")])
    with pytest.raises(ApiError) as duplicate:
        repository.find_investigation_message("SYN-INV-READ-001", "SYN-MSG-READ-001")
    assert duplicate.value.code == "CATALYST_MALFORMED_RESPONSE"
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_ID, [_message(query_plan_json="not-json")])
    with pytest.raises(ApiError) as malformed:
        repository.find_investigation_message("SYN-INV-READ-001", "SYN-MSG-READ-001")
    assert malformed.value.code == "CATALYST_MALFORMED_RESPONSE"


@pytest.mark.parametrize(("query", "method", "args", "category", "retryable", "code"), [
    (CatalystQueryName.INVESTIGATION_BY_ID, "find_investigation", ("SYN-INV-READ-001",), "timeout", True, "CATALYST_TIMEOUT"),
    (CatalystQueryName.INVESTIGATIONS_BY_OWNER, "list_investigations_for_user", ("SYN-USR-INV",), "unavailable", True, "CATALYST_UNAVAILABLE"),
    (CatalystQueryName.QUERY_HISTORY_BY_ID, "find_investigation_message", ("SYN-INV-READ-001", "SYN-MSG-READ-001"), "authentication", False, "CATALYST_AUTHORIZATION_FAILED"),
])
def test_investigation_read_transport_failures_are_translated_safely(fake, repository, query, method, args, category, retryable, code):
    fake.fail(query.value, category, retryable)
    with pytest.raises(ApiError) as error:
        getattr(repository, method)(*args)
    assert (error.value.code, error.value.retryable) == (code, retryable)
    assert all(token not in error.value.message.lower() for token in ("secret", "http", "credential", "stack"))


@pytest.mark.parametrize(("method", "args"), [
    ("create_investigation", ({},)),
    ("replace_investigation_sources", ("SYN-INV-READ-001", "[]", "2026-07-01T00:00:00+00:00")),
    ("create_investigation_message", ({},)),
    ("confirm_investigation_message", ("SYN-INV-READ-001", "SYN-MSG-READ-001", "{}")),
])
def test_investigation_and_history_writes_remain_unavailable(fake, repository, method, args):
    with pytest.raises(ApiError) as error:
        getattr(repository, method)(*args)
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
    assert fake.request_history == []


def test_sqlite_read_parity_for_investigation_and_history(app):
    sqlite = app.extensions["repository"]
    investigation = {
        "id": "SYN-INV-READ-PARITY", "user_id": "SYN-USR-INV", "title": "Parity",
        "purpose": "Active Case Investigation", "selected_sources_json": json.dumps(["CCTNS_REPLICA", "VEHICLE_REPLICA"]),
        "assigned_station": "SYN-STN-01", "assigned_district": "SYN-DST-01",
        "created_at": "2026-07-01T10:00:00+00:00", "updated_at": "2026-07-01T11:00:00+00:00",
    }
    sqlite.create_investigation(investigation)
    for message_id, created_at in (("SYN-MSG-READ-PARITY-A", "2026-07-01T10:10:00+00:00"), ("SYN-MSG-READ-PARITY-B", "2026-07-01T10:11:00+00:00")):
        sqlite.create_investigation_message({"id": message_id, "investigation_id": investigation["id"], "original_text": "synthetic", "query_plan_json": '{"intent":"SEARCH"}', "confirmed": 0, "created_at": created_at, "execution_intent": "SEARCH", "request_id": "req-parity"})
    sqlite_investigation = sqlite.find_investigation(investigation["id"])
    sqlite_messages = sqlite.list_investigation_messages(investigation["id"])
    fake = FakeCatalystClient()
    _rows(fake, CatalystQueryName.INVESTIGATION_BY_ID, [{**sqlite_investigation, "ROWID": "inv"}])
    _rows(fake, CatalystQueryName.INVESTIGATIONS_BY_OWNER, [{**sqlite_investigation, "ROWID": "inv"}])
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_ID, [{**sqlite_messages[0], "ROWID": "msg-a"}])
    _rows(fake, CatalystQueryName.QUERY_HISTORY_BY_INVESTIGATION, [{**row, "ROWID": f"msg-{index}"} for index, row in enumerate(sqlite_messages)])
    catalyst = CatalystReadOnlyRepository(CatalystReadGateway(fake), fake)
    clean = lambda record: {key: value for key, value in record.items() if key != "_catalyst_rowid"}
    assert clean(catalyst.find_investigation(investigation["id"])) == sqlite_investigation
    assert [clean(row) for row in catalyst.list_investigations_for_user("SYN-USR-INV", 10)] == [sqlite_investigation]
    assert clean(catalyst.find_investigation_message(investigation["id"], sqlite_messages[0]["id"])) == sqlite_messages[0]
    assert [clean(row) for row in catalyst.list_investigation_messages(investigation["id"])] == sqlite_messages


def test_read_slice_is_unwired_and_cannot_use_transport_sdk_credentials_or_raw_queries():
    source = Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8").lower()
    templates = Path("backend/anvaya/repositories/catalyst_templates.py").read_text(encoding="utf-8")
    for forbidden in ("import sqlite", "sqlite3", "import requests", "import urllib", "import httpx", "import socket", "import zcatalyst", "credentials_path", "os.getenv"):
        assert forbidden not in source
    assert "SELECT" not in Path("backend/anvaya/repositories/catalyst_readonly.py").read_text(encoding="utf-8")
    assert "QUERY_HISTORY_BY_INVESTIGATION" in templates
    production = Path("backend/anvaya")
    for path in list((production / "services").glob("*.py")) + list((production / "api").glob("*.py")):
        assert "CatalystReadOnlyRepository" not in path.read_text(encoding="utf-8")
        assert "FakeCatalystClient" not in path.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        create_app("testing", {"STORAGE_BACKEND": "catalyst", "CATALYST_ENABLED": True})
    with pytest.raises(ApiError) as error:
        CatalystRepositoryPlaceholder().find_investigation("SYN-INV-READ-001")
    assert error.value.code == "CATALYST_NOT_IMPLEMENTED"
