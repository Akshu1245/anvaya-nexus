from __future__ import annotations

import pytest

from backend.anvaya.repositories.catalyst_schema import (
    CATALYST_SYSTEM_COLUMNS,
    LIVE_TABLE_MAPPINGS,
    canonical_projection,
    normalize_row,
    provider_column,
    table_mapping,
)


def test_only_authorized_live_tables_are_mapped() -> None:
    assert set(LIVE_TABLE_MAPPINGS) == {
        "source_systems",
        "source_records",
        "states",
        "districts",
        "police_unit_types",
        "police_units",
        "cases",
    }


def test_source_priority_maps_to_canonical_priority() -> None:
    assert provider_column("source_systems", "priority") == "source_priority"
    assert canonical_projection("source_systems", ("id", "priority")) == "id, source_priority AS priority"
    assert normalize_row("source_systems", {"id": "SRC-1", "source_priority": "P0"}) == {
        "id": "SRC-1",
        "priority": "P0",
    }


def test_provider_system_columns_are_never_returned() -> None:
    row = {column: "provider-only" for column in CATALYST_SYSTEM_COLUMNS}
    row["id"] = "CASE-1"
    assert normalize_row("cases", row) == {"id": "CASE-1"}


def test_protected_fields_are_excluded_by_default() -> None:
    row = {"id": "REC-1", "payload_json": '{"synthetic": true}'}
    assert normalize_row("source_records", row) == {"id": "REC-1"}
    assert normalize_row("source_records", row, include_protected=True) == row


def test_unknown_tables_and_unsafe_projection_fail_closed() -> None:
    with pytest.raises(ValueError, match="not live-validated"):
        table_mapping("users")
    with pytest.raises(ValueError, match="Unsafe"):
        canonical_projection("cases", ("id; DROP TABLE cases",))
