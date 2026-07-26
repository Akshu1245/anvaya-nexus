"""Provider-safe schema mapping for the validated Catalyst Development tables.

This module is preparation only.  It contains no credentials, network client,
write path, deployment hook, or SQLite fallback.  The application-facing names
remain canonical while provider-specific table/column names are kept here.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence


CATALYST_SYSTEM_COLUMNS = frozenset({"ROWID", "CREATORID", "CREATEDTIME", "MODIFIEDTIME"})


@dataclass(frozen=True)
class CatalystTableMapping:
    canonical_name: str
    provider_name: str
    provider_to_canonical: Mapping[str, str]
    protected_columns: frozenset[str] = frozenset()

    @property
    def canonical_to_provider(self) -> Mapping[str, str]:
        return MappingProxyType({canonical: provider for provider, canonical in self.provider_to_canonical.items()})


LIVE_TABLE_MAPPINGS = MappingProxyType(
    {
        "source_systems": CatalystTableMapping(
            canonical_name="source_systems",
            provider_name="source_systems",
            provider_to_canonical=MappingProxyType({"source_priority": "priority"}),
        ),
        "source_records": CatalystTableMapping(
            canonical_name="source_records",
            provider_name="source_records",
            provider_to_canonical=MappingProxyType({}),
            protected_columns=frozenset({"payload_json"}),
        ),
        "states": CatalystTableMapping("states", "states", MappingProxyType({})),
        "districts": CatalystTableMapping("districts", "districts", MappingProxyType({})),
        "police_unit_types": CatalystTableMapping("police_unit_types", "police_unit_types", MappingProxyType({})),
        "police_units": CatalystTableMapping("police_units", "police_units", MappingProxyType({})),
        "cases": CatalystTableMapping(
            canonical_name="cases",
            provider_name="cases",
            provider_to_canonical=MappingProxyType({}),
            protected_columns=frozenset({"brief_facts"}),
        ),
    }
)


def table_mapping(canonical_name: str) -> CatalystTableMapping:
    """Return a validated live mapping; unknown tables fail closed."""
    try:
        return LIVE_TABLE_MAPPINGS[canonical_name]
    except KeyError as error:
        raise ValueError(f"Catalyst table is not live-validated: {canonical_name}") from error


def provider_column(table: str, canonical_column: str) -> str:
    mapping = table_mapping(table)
    return mapping.canonical_to_provider.get(canonical_column, canonical_column)


def canonical_projection(table: str, columns: Sequence[str]) -> str:
    """Build a fixed projection with aliases; callers cannot supply query text."""
    mapping = table_mapping(table)
    parts: list[str] = []
    for canonical in columns:
        if not canonical or not canonical.replace("_", "").isalnum():
            raise ValueError("Unsafe Catalyst projection column")
        provider = mapping.canonical_to_provider.get(canonical, canonical)
        parts.append(provider if provider == canonical else f"{provider} AS {canonical}")
    return ", ".join(parts)


def normalize_row(table: str, row: Mapping[str, Any], *, include_protected: bool = False) -> dict[str, Any]:
    """Remove provider metadata and map provider names to canonical names.

    Protected payload fields are excluded by default.  Service-layer policy and
    masking still apply after this normalization.
    """
    mapping = table_mapping(table)
    normalized: dict[str, Any] = {}
    for provider_name, value in row.items():
        if provider_name in CATALYST_SYSTEM_COLUMNS:
            continue
        canonical_name = mapping.provider_to_canonical.get(provider_name, provider_name)
        if canonical_name in mapping.protected_columns and not include_protected:
            continue
        normalized[canonical_name] = value
    return normalized
