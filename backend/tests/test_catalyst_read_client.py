from __future__ import annotations

from typing import Any, Mapping, Sequence

import pytest

from backend.anvaya.repositories.catalyst_read_client import CatalystReadClient


class FakeTransport:
    def __init__(self, rows: Sequence[Mapping[str, Any]]):
        self.rows = rows
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def execute(self, query: str, parameters: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        self.calls.append((query, parameters))
        return self.rows


def test_source_system_query_uses_live_provider_names_and_normalizes_priority() -> None:
    transport = FakeTransport([
        {"ROWID": 123, "id": "SRC-1", "name": "Synthetic Source", "source_priority": "P0"}
    ])
    client = CatalystReadClient(transport)

    rows = client.list_source_systems(limit=10)

    assert rows == [{"id": "SRC-1", "name": "Synthetic Source", "priority": "P0"}]
    query, parameters = transport.calls[0]
    assert "FROM source_systems" in query
    assert "source_priority AS priority" in query
    assert "ORDER BY source_priority ASC, id ASC" in query
    assert parameters == {"limit": 10}


def test_empty_results_return_none_without_sqlite_fallback() -> None:
    transport = FakeTransport([])
    client = CatalystReadClient(transport)

    assert client.find_case("CASE-1") is None
    assert len(transport.calls) == 1


def test_source_payload_is_hidden_unless_explicitly_requested() -> None:
    row = {"id": "REC-1", "payload_json": '{"synthetic": true}'}
    transport = FakeTransport([row])
    client = CatalystReadClient(transport)

    assert client.find_source_record("REC-1") == {"id": "REC-1"}
    assert client.find_source_record("REC-1", include_payload=True) == row


def test_invalid_ids_and_limits_fail_before_transport() -> None:
    transport = FakeTransport([])
    client = CatalystReadClient(transport)

    with pytest.raises(ValueError, match="Invalid canonical"):
        client.find_case("CASE-1' OR 1=1")
    with pytest.raises(ValueError, match="between 1 and 50"):
        client.list_source_systems(limit=51)
    assert transport.calls == []
