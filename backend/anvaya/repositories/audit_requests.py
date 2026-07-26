from __future__ import annotations

from dataclasses import dataclass


AUDIT_ROLES = ("INVESTIGATOR", "CRIME_ANALYST", "SUPERVISOR")


@dataclass(frozen=True)
class AuditEventInput:
    id: str
    event_type: str
    outcome: str
    user_id: str | None
    request_id: str | None
    safe_metadata_json: str
    occurred_at: str

    def __post_init__(self) -> None:
        if not self.id or not self.event_type or not self.outcome or not self.occurred_at:
            raise ValueError("Audit event requires ID, type, outcome, and timestamp")


@dataclass(frozen=True)
class AuditEventFilter:
    actor_user_id: str | None = None
    actor_role: str | None = None
    investigation_id: str | None = None
    report_id: str | None = None
    event_type: str | None = None
    outcome: str | None = None
    request_id: str | None = None
    start: str | None = None
    end: str | None = None
    limit: int = 25
    offset: int = 0

    def __post_init__(self) -> None:
        if self.actor_role is not None and self.actor_role not in AUDIT_ROLES:
            raise ValueError("Audit role is invalid")
        if not 1 <= self.limit <= 50:
            raise ValueError("Audit limit must be between 1 and 50")
        if self.offset < 0:
            raise ValueError("Audit offset cannot be negative")
