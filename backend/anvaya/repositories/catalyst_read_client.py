"""Read-only Catalyst Data Store integration seam.

The transport is injected by a future AppSail/bootstrap layer.  This module does
not obtain credentials, call Catalyst directly, seed rows, or implement writes.
Only fixed queries for the seven live-validated Development tables are allowed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from backend.anvaya.repositories.catalyst_schema import canonical_projection, normalize_row, table_mapping


class CatalystQueryTransport(Protocol):
    def execute(self, query: str, parameters: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        """Execute one server-owned read query and return provider rows."""


@dataclass(frozen=True)
class CatalystReadClient:
    transport: CatalystQueryTransport

    def list_source_systems(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded = _bounded_limit(limit, maximum=50)
        columns = (
            "id", "name", "source_tier", "access_class", "reliability_role", "status",
            "last_successful_sync", "freshness_threshold_hours", "version", "connector_type",
            "description", "priority",
        )
        query = (
            f"SELECT {canonical_projection('source_systems', columns)} "
            "FROM source_systems ORDER BY source_priority ASC, id ASC LIMIT 0,:limit"
        )
        return self._rows("source_systems", query, {"limit": bounded})

    def find_source_system(self, source_id: str) -> dict[str, Any] | None:
        canonical_id = _canonical_id(source_id)
        columns = (
            "id", "name", "source_tier", "access_class", "reliability_role", "status",
            "last_successful_sync", "freshness_threshold_hours", "version", "connector_type",
            "description", "priority",
        )
        query = (
            f"SELECT {canonical_projection('source_systems', columns)} "
            "FROM source_systems WHERE id = :id LIMIT 0,1"
        )
        return self._one("source_systems", query, {"id": canonical_id})

    def find_case(self, case_id: str) -> dict[str, Any] | None:
        canonical_id = _canonical_id(case_id)
        columns = (
            "id", "crime_number", "registered_at", "source_record_id", "case_number", "fir_number",
            "incident_from_at", "incident_to_at", "information_received_at", "latitude", "longitude",
            "brief_facts", "case_category_id", "gravity_offence_id", "crime_major_head_id",
            "crime_minor_head_id", "case_status_id", "state_id", "canonical_district_id",
            "police_unit_id", "registering_officer_id", "court_id",
        )
        query = f"SELECT {canonical_projection('cases', columns)} FROM cases WHERE id = :id LIMIT 0,1"
        return self._one("cases", query, {"id": canonical_id})

    def find_source_record(self, record_id: str, *, include_payload: bool = False) -> dict[str, Any] | None:
        canonical_id = _canonical_id(record_id)
        columns = (
            "id", "source_system_id", "external_id", "version", "source_updated_at", "imported_at",
            "access_class", "reliability_role", "freshness_state", "checksum", "payload_json",
        )
        query = f"SELECT {canonical_projection('source_records', columns)} FROM source_records WHERE id = :id LIMIT 0,1"
        rows = self.transport.execute(query, {"id": canonical_id})
        if not rows:
            return None
        return normalize_row("source_records", rows[0], include_protected=include_payload)

    def _rows(self, table: str, query: str, parameters: Mapping[str, Any]) -> list[dict[str, Any]]:
        table_mapping(table)
        return [normalize_row(table, row) for row in self.transport.execute(query, parameters)]

    def _one(self, table: str, query: str, parameters: Mapping[str, Any]) -> dict[str, Any] | None:
        rows = self._rows(table, query, parameters)
        return rows[0] if rows else None


def _canonical_id(value: str) -> str:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized or len(normalized) > 100 or not all(character.isalnum() or character in "-_" for character in normalized):
        raise ValueError("Invalid canonical Catalyst ID")
    return normalized


def _bounded_limit(value: int, *, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximum:
        raise ValueError(f"Catalyst limit must be between 1 and {maximum}")
    return value
