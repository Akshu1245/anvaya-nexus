"""Offline-only query gateway; it is intentionally not a Repository adapter."""
from __future__ import annotations

from typing import Any, Mapping

from backend.anvaya.api.errors import ApiError
from backend.anvaya.platform.catalyst_client import CatalystDataStoreClient
from backend.anvaya.platform.catalyst_errors import CatalystClientFailure, translate_catalyst_failure
from backend.anvaya.repositories.catalyst_binding import bind_parameters
from backend.anvaya.repositories.catalyst_rows import extract_rows, normalize_row
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName, CatalystQueryRequest, CatalystTemplateRegistry, DEFAULT_CATALYST_TEMPLATES


class CatalystReadGateway:
    """Execute only registered offline read requests via an injected client."""

    def __init__(self, client: CatalystDataStoreClient, registry: CatalystTemplateRegistry = DEFAULT_CATALYST_TEMPLATES):
        self._client = client
        self._registry = registry

    def read(self, name: CatalystQueryName | str, parameters: Mapping[str, Any]) -> list[dict[str, Any]]:
        template = self._registry.get(name)
        if template.operation.value != "read":
            raise ApiError("CATALYST_QUERY_UNSUPPORTED", "This Catalyst query is not supported.", 400, False)
        request = CatalystQueryRequest(query=template, parameters=bind_parameters(template, parameters))
        try:
            envelope = self._client.execute_read(request)
        except CatalystClientFailure as error:
            raise translate_catalyst_failure(error) from error
        rows = extract_rows(envelope)
        if len(rows) > template.max_results:
            raise ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)
        return [normalize_row(template.result_shape, row) for row in rows]
