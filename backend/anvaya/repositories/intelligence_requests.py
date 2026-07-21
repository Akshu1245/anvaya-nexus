from __future__ import annotations

from dataclasses import dataclass


INTELLIGENCE_SOURCE_IDS = ("CCTNS_REPLICA",)
GRAPH_RELATIONSHIP_TYPES = (
    "RECORDED_DEVICE",
    "SHARED_IMEI",
    "RECORDED_PHONE",
    "RECORDED_VEHICLE",
)


@dataclass(frozen=True)
class CaseDnaRequest:
    """Trusted fixed case pair for deterministic similarity inputs."""

    left_case_id: str
    right_case_id: str
    source_system_ids: tuple[str, ...] = INTELLIGENCE_SOURCE_IDS

    def __post_init__(self) -> None:
        if not self.left_case_id or not self.right_case_id:
            raise ValueError("Case DNA requires two case IDs")
        if not self.source_system_ids:
            raise ValueError("Case DNA requires at least one source")
        object.__setattr__(self, "source_system_ids", tuple(dict.fromkeys(self.source_system_ids)))


@dataclass(frozen=True)
class EvidenceGraphRequest:
    """Trusted bounded request for the current case-centred evidence graph."""

    case_id: str
    source_system_ids: tuple[str, ...] = INTELLIGENCE_SOURCE_IDS
    relationship_types: tuple[str, ...] = GRAPH_RELATIONSHIP_TYPES
    node_limit: int = 20
    edge_limit: int = 20

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("Evidence graph requires a case ID")
        if not self.source_system_ids:
            raise ValueError("Evidence graph requires at least one source")
        object.__setattr__(self, "source_system_ids", tuple(dict.fromkeys(self.source_system_ids)))
        if not self.relationship_types or any(value not in GRAPH_RELATIONSHIP_TYPES for value in self.relationship_types):
            raise ValueError("Evidence graph relationship type is not allowed")
        if len(set(self.relationship_types)) != len(self.relationship_types):
            raise ValueError("Evidence graph relationship types must be unique")
        if not 1 <= self.node_limit <= 20 or not 1 <= self.edge_limit <= 20:
            raise ValueError("Evidence graph limits must be between 1 and 20")
