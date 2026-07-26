"""Dependency-injected, offline client protocol for future Catalyst transport."""
from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Protocol

from backend.anvaya.repositories.catalyst_templates import CatalystQueryRequest


class CatalystTableName(str, Enum):
    """Trusted manifest table identifiers; callers cannot supply arbitrary names."""

    USERS = "anvaya_users"
    SESSIONS = "anvaya_sessions"
    SOURCE_SYSTEMS = "anvaya_source_systems"
    SOURCE_RECORDS = "anvaya_source_records"
    SCHEMA_VERSIONS = "anvaya_schema_versions"


class CatalystDataStoreClient(Protocol):
    def execute_read(self, request: CatalystQueryRequest) -> Mapping[str, Any]: ...
    def execute_write(self, request: CatalystQueryRequest) -> Mapping[str, Any]: ...
    def insert_row(self, table_name: CatalystTableName, values: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def update_row(self, table_name: CatalystTableName, canonical_id: str, values: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def delete_row(self, table_name: CatalystTableName, canonical_id: str) -> None: ...
    def get_row_by_canonical_id(self, table_name: CatalystTableName, canonical_id: str) -> Mapping[str, Any] | None: ...
    def health_check(self) -> Mapping[str, Any]: ...
    def close(self) -> None: ...
