from __future__ import annotations

from dataclasses import dataclass


RELATIONSHIP_TYPES = (
    "RECORDED_DEVICE",
    "SHARED_IMEI",
    "RECORDED_PHONE",
    "RECORDED_VEHICLE",
)


@dataclass(frozen=True)
class DiscoveryRequest:
    seed_case_ids: tuple[str, ...]
    source_system_ids: tuple[str, ...]
    limit: int = 25
    offset: int = 0

    def __post_init__(self) -> None:
        if not self.seed_case_ids:
            raise ValueError("Discovery requires at least one seed case")
        if not self.source_system_ids:
            raise ValueError("Discovery requires at least one source")
        if len(set(self.seed_case_ids)) != len(self.seed_case_ids):
            raise ValueError("Discovery seed case IDs must be unique")
        if len(set(self.source_system_ids)) != len(self.source_system_ids):
            raise ValueError("Discovery source IDs must be unique")
        if not 1 <= self.limit <= 25:
            raise ValueError("Discovery limit must be between 1 and 25")
        if self.offset < 0:
            raise ValueError("Discovery offset cannot be negative")


@dataclass(frozen=True)
class RelationshipPathRequest:
    source_system_ids: tuple[str, ...] = ("CCTNS_REPLICA",)
    relationship_types: tuple[str, ...] = RELATIONSHIP_TYPES
    max_depth: int = 3
    edge_limit: int = 200

    def __post_init__(self) -> None:
        if not 1 <= self.max_depth <= 3:
            raise ValueError("Relationship path depth must be between 1 and 3")
        if not 1 <= self.edge_limit <= 200:
            raise ValueError("Relationship edge limit must be between 1 and 200")
        if not self.relationship_types or any(value not in RELATIONSHIP_TYPES for value in self.relationship_types):
            raise ValueError("Relationship type is not allowed")
        if len(set(self.relationship_types)) != len(self.relationship_types):
            raise ValueError("Relationship types must be unique")
        if len(set(self.source_system_ids)) != len(self.source_system_ids):
            raise ValueError("Relationship source IDs must be unique")
        if not self.source_system_ids:
            raise ValueError("Relationship paths require at least one source")
