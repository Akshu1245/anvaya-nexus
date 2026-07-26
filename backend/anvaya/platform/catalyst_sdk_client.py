"""Provider-specific, read-only Catalyst Python SDK transport for AppSail.

The client is deliberately request-scoped: AppSail initializes the Catalyst SDK
from the incoming Flask request, and this transport resolves that initialized
application only when a read is executed. It never accepts caller-supplied query
text, never performs writes, and currently exposes only the live-validated
Development source-system reads needed for health and capability validation.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from backend.anvaya.platform.catalyst_client import CatalystDataStoreClient, CatalystTableName
from backend.anvaya.platform.catalyst_errors import CatalystClientFailure
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName, CatalystQueryRequest


class CatalystSdkDataStoreClient(CatalystDataStoreClient):
    """Execute a minimal allowlisted read slice through the Catalyst Python SDK."""

    def __init__(self, app_provider: Callable[[], Any]):
        self._app_provider = app_provider

    def execute_read(self, request: CatalystQueryRequest) -> Mapping[str, Any]:
        try:
            query = self._render_query(request)
            catalyst_app = self._app_provider()
            zcql_service = catalyst_app.zcql()
            result = zcql_service.execute_query(query)
            return {"status": "success", "data": self._normalize_rows(result)}
        except CatalystClientFailure:
            raise
        except TimeoutError as error:
            raise CatalystClientFailure("timeout", True) from error
        except PermissionError as error:
            raise CatalystClientFailure("authentication", False) from error
        except Exception as error:  # Provider details must never cross this boundary.
            raise CatalystClientFailure("unavailable", True) from error

    def health_check(self) -> Mapping[str, Any]:
        try:
            catalyst_app = self._app_provider()
            result = catalyst_app.zcql().execute_query("SELECT id FROM source_systems LIMIT 0,1")
            self._normalize_rows(result)
            # Keep the existing repository health contract stable while this
            # Development transport remains intentionally read-only.
            return {"status": "offline_ok"}
        except CatalystClientFailure:
            raise
        except TimeoutError as error:
            raise CatalystClientFailure("timeout", True) from error
        except PermissionError as error:
            raise CatalystClientFailure("authentication", False) from error
        except Exception as error:
            raise CatalystClientFailure("unavailable", True) from error

    def execute_write(self, request: CatalystQueryRequest) -> Mapping[str, Any]:
        raise CatalystClientFailure("unsupported_query", False)

    def insert_row(self, table_name: CatalystTableName, values: Mapping[str, Any]) -> Mapping[str, Any]:
        raise CatalystClientFailure("unsupported_query", False)

    def update_row(self, table_name: CatalystTableName, canonical_id: str, values: Mapping[str, Any]) -> Mapping[str, Any]:
        raise CatalystClientFailure("unsupported_query", False)

    def delete_row(self, table_name: CatalystTableName, canonical_id: str) -> None:
        raise CatalystClientFailure("unsupported_query", False)

    def get_row_by_canonical_id(self, table_name: CatalystTableName, canonical_id: str) -> Mapping[str, Any] | None:
        raise CatalystClientFailure("unsupported_query", False)

    def close(self) -> None:
        # The SDK application is request-scoped and owned by Catalyst/AppSail.
        return None

    @staticmethod
    def _render_query(request: CatalystQueryRequest) -> str:
        values = request.parameters.values
        if request.query.name is CatalystQueryName.SOURCE_SYSTEM_LIST:
            limit = values["limit"]
            return (
                "SELECT id, name, source_tier, access_class, reliability_role, status, "
                "last_successful_sync, freshness_threshold_hours, version, connector_type, "
                f"description, source_priority FROM source_systems ORDER BY source_priority ASC, id ASC LIMIT 0,{limit}"
            )
        if request.query.name is CatalystQueryName.SOURCE_SYSTEM_BY_ID:
            source_id = CatalystSdkDataStoreClient._quote(values["id"])
            return (
                "SELECT id, name, source_tier, access_class, reliability_role, status, "
                "last_successful_sync, freshness_threshold_hours, version, connector_type, "
                f"description, source_priority FROM source_systems WHERE id = {source_id} LIMIT 0,1"
            )
        raise CatalystClientFailure("not_verified", False)

    @staticmethod
    def _quote(value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 128:
            raise CatalystClientFailure("invalid_parameters", False)
        return "'" + value.replace("'", "''") + "'"

    @staticmethod
    def _normalize_rows(result: Any) -> list[dict[str, Any]]:
        if result is None:
            return []
        if not isinstance(result, Sequence) or isinstance(result, (str, bytes, bytearray)):
            raise CatalystClientFailure("malformed_response", True)
        rows: list[dict[str, Any]] = []
        for item in result:
            if not isinstance(item, Mapping):
                raise CatalystClientFailure("malformed_response", True)
            row: Mapping[str, Any] = item
            # Catalyst ZCQL commonly wraps each record under its table name.
            if len(item) == 1:
                candidate = next(iter(item.values()))
                if isinstance(candidate, Mapping):
                    row = candidate
            normalized = dict(row)
            if "source_priority" in normalized and "priority" not in normalized:
                normalized["priority"] = normalized.pop("source_priority")
            rows.append(normalized)
        return rows
