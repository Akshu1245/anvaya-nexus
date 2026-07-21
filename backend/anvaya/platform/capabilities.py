from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class CapabilityState(str, Enum):
    DISABLED = "disabled"
    CONFIGURED = "configured"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    AVAILABLE = "available"


@dataclass(frozen=True)
class Capability:
    name: str
    state: CapabilityState
    detail: str

    def safe_dict(self) -> dict[str, str]:
        return {"name": self.name, "state": self.state.value, "detail": self.detail}


@dataclass(frozen=True)
class CapabilitySummary:
    capabilities: tuple[Capability, ...]

    def safe_dict(self) -> dict[str, list[dict[str, str]]]:
        return {"capabilities": [capability.safe_dict() for capability in self.capabilities]}

