from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from backend.anvaya.platform.catalyst_errors import CatalystClientFailure
from backend.anvaya.platform.catalyst_client import CatalystTableName
from backend.anvaya.repositories.catalyst_templates import CatalystQueryRequest


class FakeCatalystClient:
    """Strict in-memory client; it has no network, SDK, or SQLite dependency."""

    def __init__(self):
        self._responses: dict[str, Mapping[str, Any]] = {}
        self._failures: dict[str, CatalystClientFailure] = {}
        self.request_history: list[CatalystQueryRequest] = []
        self._health_response: Mapping[str, Any] = {"status": "offline_ok"}
        self._health_failure: CatalystClientFailure | None = None

    def register_response(self, query_name: str, envelope: Mapping[str, Any]) -> None:
        self._responses[query_name] = deepcopy(dict(envelope))

    def register_rows(self, query_name: str, rows: list[Mapping[str, Any]]) -> None:
        self.register_response(query_name, {"status": "success", "data": {"rows": rows}})

    def fail(self, query_name: str, category: str, retryable: bool = False) -> None:
        self._failures[query_name] = CatalystClientFailure(category, retryable)

    def set_health_response(self, envelope: Mapping[str, Any]) -> None:
        self._health_response = deepcopy(dict(envelope))
        self._health_failure = None

    def fail_health(self, category: str, retryable: bool = False) -> None:
        self._health_failure = CatalystClientFailure(category, retryable)

    def execute_read(self, request: CatalystQueryRequest) -> Mapping[str, Any]:
        name = request.query.name.value
        self.request_history.append(request)
        if name in self._failures:
            raise self._failures[name]
        if name not in self._responses:
            raise CatalystClientFailure("unsupported_query")
        return deepcopy(self._responses[name])

    def execute_write(self, request: CatalystQueryRequest) -> Mapping[str, Any]:
        raise CatalystClientFailure("not_implemented")

    def insert_row(self, table_name: CatalystTableName, values: Mapping[str, Any]) -> Mapping[str, Any]:
        raise CatalystClientFailure("not_implemented")

    def update_row(self, table_name: CatalystTableName, canonical_id: str, values: Mapping[str, Any]) -> Mapping[str, Any]:
        raise CatalystClientFailure("not_implemented")

    def delete_row(self, table_name: CatalystTableName, canonical_id: str) -> None:
        raise CatalystClientFailure("not_implemented")

    def get_row_by_canonical_id(self, table_name: CatalystTableName, canonical_id: str) -> Mapping[str, Any] | None:
        raise CatalystClientFailure("not_implemented")

    def health_check(self) -> Mapping[str, Any]:
        if self._health_failure:
            raise self._health_failure
        return deepcopy(self._health_response)

    def close(self) -> None:
        return None
