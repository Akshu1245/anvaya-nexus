from __future__ import annotations

from dataclasses import dataclass

from backend.anvaya.repositories.person_roles import CASE_PERSON_ROLES


@dataclass(frozen=True)
class CaseSearchFilter:
    """Trusted, server-built filter for the current deterministic SEARCH path."""

    offence: str | None = None
    status: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    case_identifier: str | None = None
    location: str | None = None
    phone: str | None = None
    imei: str | None = None
    vehicle_registration: str | None = None
    person_name: str | None = None
    person_role: str | None = None
    act_id: str | None = None
    act_code: str | None = None
    section_id: str | None = None
    section_code: str | None = None
    case_category: str | None = None
    gravity_offence: str | None = None
    crime_major_head: str | None = None
    crime_minor_head: str | None = None
    canonical_case_status: str | None = None
    arrest_event_type: str | None = None
    chargesheet_report_type: str | None = None
    has_arrest_event: bool | None = None
    has_chargesheet: bool | None = None
    state: str | None = None
    district: str | None = None
    police_unit: str | None = None
    registering_officer: str | None = None
    court: str | None = None
    crime_number: str | None = None
    case_number: str | None = None
    registration_date_from: str | None = None
    registration_date_to: str | None = None
    source_system_ids: tuple[str, ...] = ()
    limit: int = 25
    offset: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 25:
            raise ValueError("Search limit must be between 1 and 25")
        if self.offset < 0:
            raise ValueError("Search offset cannot be negative")
        for lower, upper in ((self.date_from, self.date_to), (self.registration_date_from, self.registration_date_to)):
            if lower and upper and lower > upper:
                raise ValueError("Search date range is invalid")
        if len(set(self.source_system_ids)) != len(self.source_system_ids):
            raise ValueError("Search source IDs must be unique")
        if self.person_role is not None and self.person_role not in CASE_PERSON_ROLES:
            raise ValueError("Search person role is not allowed")
        if self.person_name is not None:
            if not 1 <= len(self.person_name.strip()) <= 80 or any(value in self.person_name for value in ("%", "_")):
                raise ValueError("Search person name is invalid")
        for value in (self.act_id, self.act_code, self.section_id, self.section_code, self.case_category, self.gravity_offence, self.crime_major_head, self.crime_minor_head, self.canonical_case_status):
            if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 64):
                raise ValueError("Search legal or classification filter is invalid")
        if self.arrest_event_type is not None and self.arrest_event_type not in {"ARREST", "SURRENDER"}:
            raise ValueError("Search arrest event type is not allowed")
        if self.chargesheet_report_type is not None and self.chargesheet_report_type not in {"A_CHARGESHEET", "B_FALSE", "C_UNDETECTED"}:
            raise ValueError("Search chargesheet report type is not allowed")
        for value in (self.has_arrest_event, self.has_chargesheet):
            if value is not None and not isinstance(value, bool):
                raise ValueError("Search event presence filter must be boolean")
        for value in (self.state, self.district, self.police_unit, self.registering_officer, self.court):
            if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 64):
                raise ValueError("Search organisation filter is invalid")
        for value in (self.crime_number, self.case_number, self.case_identifier):
            if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 64 or any(token in value for token in ("%", "_"))):
                raise ValueError("Search identifier is invalid")
