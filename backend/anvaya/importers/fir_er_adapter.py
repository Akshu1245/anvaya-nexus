"""Deterministic synthetic FIR ER-like input to ANVAYA canonical rows.

This module performs no I/O and is not an official or live FIR integration.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime


TOP_LEVEL_FIELDS = {
    "synthetic_data_only", "fir_number", "crime_number", "case_number", "registered_at",
    "occurrence", "police_station", "district", "state", "sections", "people",
    "vehicles", "properties", "evidence", "offence", "brief_facts", "investigation_status", "source",
}
ROLES = {"COMPLAINANT", "VICTIM", "ACCUSED"}


def _required(mapping, key, context="record"):
    value = mapping.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{context}.{key} is required")
    return value.strip() if isinstance(value, str) else value


def _synthetic_id(value, field):
    value = str(value).strip()
    if not value.startswith("SYN-"):
        raise ValueError(f"{field} must be a synthetic identifier")
    return value


def _date(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be an ISO 8601 date-time") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.isoformat()


def _unique_ids(items, collection):
    seen = set()
    for item in items:
        identifier = _synthetic_id(_required(item, "id", collection), f"{collection}.id")
        if identifier in seen:
            raise ValueError(f"duplicate identifier in {collection}: {identifier}")
        seen.add(identifier)


def _source_id(item, default):
    return _synthetic_id(item.get("source_record_id", default), "source_record_id")


def adapt_fir_er(record):
    """Validate one synthetic FIR ER-like mapping and return canonical row groups."""
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    if record.get("synthetic_data_only") is not True:
        raise ValueError("synthetic_data_only must be true")

    source = _required(record, "source")
    if not isinstance(source, dict):
        raise ValueError("record.source must be an object")
    source_system_id = _synthetic_id(_required(source, "system_id", "source"), "source.system_id")
    source_record_id = _synthetic_id(_required(source, "record_id", "source"), "source.record_id")
    external_id = _synthetic_id(_required(source, "external_id", "source"), "source.external_id")
    fir_number = _synthetic_id(_required(record, "fir_number"), "fir_number")

    station = _required(record, "police_station")
    district = _required(record, "district")
    state = _required(record, "state")
    occurrence = _required(record, "occurrence")
    for name, value in (("police_station", station), ("district", district), ("state", state), ("occurrence", occurrence)):
        if not isinstance(value, dict):
            raise ValueError(f"record.{name} must be an object")

    registered_at = _date(_required(record, "registered_at"), "registered_at")
    occurrence_from = _date(_required(occurrence, "from_at", "occurrence"), "occurrence.from_at")
    occurrence_to = _date(occurrence.get("to_at", occurrence_from), "occurrence.to_at")
    if occurrence_from > occurrence_to or occurrence_to > registered_at:
        raise ValueError("occurrence and registration dates are out of order")

    collections = {name: record.get(name, []) for name in ("sections", "people", "vehicles", "properties", "evidence")}
    if not all(isinstance(items, list) and all(isinstance(item, dict) for item in items) for items in collections.values()):
        raise ValueError("sections, people, vehicles, properties, and evidence must be arrays of objects")
    for name, items in collections.items():
        _unique_ids(items, name)

    location = occurrence.get("location") or {}
    location_id = _synthetic_id(_required(location, "id", "occurrence.location"), "occurrence.location.id")
    latitude, longitude = location.get("latitude"), location.get("longitude")
    if (latitude is None) != (longitude is None):
        raise ValueError("occurrence.location coordinates must be supplied as a pair")
    if latitude is not None:
        try:
            latitude, longitude = float(latitude), float(longitude)
        except (TypeError, ValueError) as error:
            raise ValueError("occurrence.location coordinates must be numeric") from error
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("occurrence.location coordinates are out of range")
    case_id = "SYN-CASE-FIRER-" + hashlib.sha256(f"{source_system_id}:{external_id}".encode()).hexdigest()[:12].upper()
    source_updated_at = _date(_required(source, "updated_at", "source"), "source.updated_at")
    imported_at = _date(source.get("imported_at", source_updated_at), "source.imported_at")

    people = []
    roles = []
    for sequence, item in enumerate(collections["people"], 1):
        role = str(_required(item, "role", "people")).upper()
        if role not in ROLES:
            raise ValueError(f"unsupported person role: {role}")
        person_id = _synthetic_id(item["id"], "people.id")
        item_source = _source_id(item, source_record_id)
        people.append({"id": person_id, "display_name": str(_required(item, "display_name", "people")), "source_record_id": item_source})
        roles.append({"id": f"SYN-CPR-{case_id[13:]}-{sequence:02d}", "case_id": case_id, "person_id": person_id, "role": role, "role_sequence": sequence, "source_record_id": item_source})

    legal_sections = []
    for sequence, item in enumerate(collections["sections"], 1):
        legal_sections.append({
            "id": _synthetic_id(item["id"], "sections.id"), "case_id": case_id,
            "act_id": _synthetic_id(_required(item, "act_id", "sections"), "sections.act_id"),
            "section_id": _synthetic_id(_required(item, "section_id", "sections"), "sections.section_id"),
            "act_order": sequence, "section_order": sequence, "source_record_id": _source_id(item, source_record_id),
        })

    vehicles = [{
        "id": _synthetic_id(item["id"], "vehicles.id"),
        "synthetic_registration": _synthetic_id(_required(item, "registration", "vehicles"), "vehicles.registration"),
        "vehicle_type": str(item.get("type", "SYNTHETIC_VEHICLE")), "colour": str(item.get("colour", "NOT_RECORDED")),
        "source_record_id": _source_id(item, source_record_id),
    } for item in collections["vehicles"]]

    evidence = [{
        "id": _synthetic_id(item["id"], "evidence.id"), "case_id": case_id,
        "evidence_type": str(item.get("type", "SYNTHETIC_ITEM")), "description": str(item.get("description", "Synthetic evidence reference")),
        "status": str(item.get("status", "AVAILABLE")), "sensitivity": str(item.get("sensitivity", "RESTRICTED")),
        "source_record_id": _source_id(item, source_record_id),
    } for item in collections["evidence"]]
    evidence.extend({
        "id": _synthetic_id(item["id"], "properties.id"), "case_id": case_id,
        "evidence_type": "SYNTHETIC_PROPERTY_REFERENCE", "description": str(item.get("description", "Synthetic property reference")),
        "status": "REFERENCED", "sensitivity": "RESTRICTED", "source_record_id": _source_id(item, source_record_id),
    } for item in collections["properties"])

    canonical_payload = {
        "synthetic_data_only": True, "fir_number": fir_number, "external_id": external_id,
        "registered_at": registered_at, "occurrence_from_at": occurrence_from, "occurrence_to_at": occurrence_to,
    }
    payload_json = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    crime_number = _synthetic_id(record["crime_number"], "crime_number") if record.get("crime_number") else fir_number
    case_number = _synthetic_id(record["case_number"], "case_number") if record.get("case_number") else None
    return {
        "case": {
            "id": case_id, "fir_number": fir_number, "crime_number": crime_number,
            "case_number": case_number, "station_id": _synthetic_id(_required(station, "id", "police_station"), "police_station.id"),
            "district_id": _synthetic_id(_required(district, "id", "district"), "district.id"),
            "state_id": _synthetic_id(_required(state, "id", "state"), "state.id"),
            "canonical_district_id": _synthetic_id(district["id"], "district.id"), "police_unit_id": _synthetic_id(station["id"], "police_station.id"),
            "offence": str(record.get("offence", "NOT_RECORDED")), "incident_at": occurrence_from,
            "incident_from_at": occurrence_from, "incident_to_at": occurrence_to, "registered_at": registered_at,
            "brief_facts": record.get("brief_facts"), "status": str(record.get("investigation_status", "NOT_RECORDED")),
            "source_record_id": source_record_id,
        },
        "location": None if latitude is None else {"id": location_id, "locality": str(location.get("locality", "NOT_RECORDED")), "station_id": station["id"], "district_id": district["id"], "latitude": latitude, "longitude": longitude, "source_record_id": _source_id(location, source_record_id)},
        "people": people, "case_person_roles": roles, "case_legal_sections": legal_sections,
        "vehicles": vehicles, "evidence_records": evidence,
        "source_record": {
            "id": source_record_id, "source_system_id": source_system_id, "external_id": external_id,
            "version": str(source.get("version", "synthetic-fir-er-1")), "source_updated_at": source_updated_at,
            "imported_at": imported_at, "access_class": "RESTRICTED", "reliability_role": "Synthetic FIR ER-like source",
            "freshness_state": "Fresh", "checksum": hashlib.sha256(payload_json.encode()).hexdigest(), "payload_json": payload_json,
        },
        "synthetic_data_only": True,
        "unsupported_fields": sorted(set(record) - TOP_LEVEL_FIELDS),
    }
