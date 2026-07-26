"""Normalize a deliberately small, safe set of Catalyst-like result rows."""
from __future__ import annotations

import json
from typing import Any, Mapping

from backend.anvaya.api.errors import ApiError

_SYSTEM_FIELDS = {"ROWID", "CREATORID", "CREATEDTIME", "MODIFIEDTIME"}

_SHAPES: dict[str, tuple[tuple[str, ...], frozenset[str], dict[str, str]]] = {
    "user": (("id", "username", "password_hash", "role", "assigned_station", "assigned_district", "active"), frozenset({"assigned_station", "assigned_district"}), {"active": "boolean"}),
    "source_system": (("id", "name", "source_tier", "access_class", "reliability_role", "status", "last_successful_sync", "freshness_threshold_hours", "version", "connector_type", "description", "priority"), frozenset({"last_successful_sync"}), {"freshness_threshold_hours": "integer"}),
    "case": (("id", "fir_number", "crime_number", "station_id", "district_id", "offence", "incident_at", "registered_at", "status", "source_record_id"), frozenset(), {}),
    "source_record": (("id", "source_system_id", "external_id", "version", "source_updated_at", "imported_at", "access_class", "reliability_role", "freshness_state", "checksum", "payload_json"), frozenset(), {}),
    "schema_state": (("version",), frozenset({"version"}), {"version": "integer"}),
    "investigation": (("id", "user_id", "title", "purpose", "selected_sources_json", "assigned_station", "assigned_district", "created_at", "updated_at"), frozenset({"assigned_station", "assigned_district"}), {}),
    "query_history": (("id", "original_text", "query_plan_json", "confirmed", "parent_message_id", "execution_intent", "result_count", "request_id", "created_at"), frozenset({"parent_message_id", "execution_intent", "result_count", "request_id"}), {"confirmed": "boolean"}),
    "search_candidate": (("id", "fir_number", "crime_number", "station_id", "district_id", "offence", "incident_at", "registered_at", "status", "source_record_id", "freshness_state", "source_system_id", "reliability_role", "access_class"), frozenset(), {}),
    "discovery_candidate": (("base_case_id", "target_type", "relationship_type", "edge_source_record_id", "candidate_id", "link_source_record_id", "id", "fir_number", "crime_number", "station_id", "district_id", "offence", "incident_at", "registered_at", "status", "source_record_id", "freshness_state", "source_system_id", "reliability_role", "access_class"), frozenset(), {}),
    "relationship_edge": (("id", "source_type", "source_id", "target_type", "target_id", "relationship_type", "edge_class", "source_record_id", "freshness_state", "reliability_role", "access_class", "source_system_id"), frozenset(), {}),
    "case_360_entity": (("edge_id", "case_id", "target_type", "target_id", "edge_source_record_id", "value", "entity_source_record_id"), frozenset({"value", "entity_source_record_id"}), {}),
    "case_360_evidence": (("id", "case_id", "evidence_type", "description", "status", "sensitivity", "source_record_id"), frozenset(), {}),
    "case_360_forensic": (("id", "case_id", "event_type", "occurred_at", "result_status", "source_record_id"), frozenset(), {}),
    "case_360_trust_issue": (("id", "case_id", "issue_type", "severity", "description", "source_record_ids_json", "status"), frozenset({"case_id"}), {}),
    "source_passport_record": (("id", "source_system_id", "external_id", "version", "source_updated_at", "imported_at", "access_class", "reliability_role", "freshness_state", "checksum", "payload_json", "source_name", "limitations"), frozenset({"limitations"}), {}),
    "source_transformation": (("operation", "source_field", "target_field", "rule_version", "occurred_at", "outcome"), frozenset({"source_field", "target_field"}), {}),
    "intelligence_edge": (("id", "source_type", "source_id", "target_type", "target_id", "relationship_type", "edge_class", "source_record_id"), frozenset(), {}),
    "report": (("id", "investigation_id", "owner_user_id", "assigned_reviewer_id", "title", "status", "current_version", "created_at", "updated_at"), frozenset({"assigned_reviewer_id"}), {"current_version": "integer"}),
    "report_list": (("id", "investigation_id", "owner_user_id", "assigned_reviewer_id", "title", "status", "current_version", "created_at", "updated_at", "owner_name", "reviewer_name"), frozenset({"assigned_reviewer_id", "reviewer_name"}), {"current_version": "integer"}),
    "eligible_supervisor": (("id", "username", "role"), frozenset(), {}),
    "eligible_supervisor_list": (("username", "role"), frozenset(), {}),
    "report_version": (("id", "report_id", "version_number", "status", "sections_json", "notes", "html", "created_by", "created_at", "immutable"), frozenset(), {"version_number": "integer", "immutable": "boolean"}),
    "report_review": (("decision", "note", "created_at", "username", "version_number"), frozenset(), {"version_number": "integer"}),
}


def _malformed() -> ApiError:
    return ApiError("CATALYST_MALFORMED_RESPONSE", "Catalyst returned an invalid response.", 502, True)


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.lower() in {"true", "false", "0", "1"}:
        return value.lower() in {"true", "1"}
    raise _malformed()


def _integer(value: Any) -> int:
    if isinstance(value, bool):
        raise _malformed()
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise _malformed() from error


def _canonical_source_snapshot(value: Any) -> str:
    if not isinstance(value, str):
        raise _malformed()
    try:
        source_ids = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise _malformed() from error
    if not isinstance(source_ids, list) or any(not isinstance(item, str) or not item or not item.replace("_", "").replace("-", "").isalnum() for item in source_ids):
        raise _malformed()
    if len(source_ids) != len(set(source_ids)):
        raise _malformed()
    return value


def _json_text(value: Any) -> str:
    if not isinstance(value, str):
        raise _malformed()
    try:
        json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise _malformed() from error
    return value


def normalize_row(shape: str, row: Mapping[str, Any]) -> dict[str, Any]:
    try:
        required, nullable, conversions = _SHAPES[shape]
    except KeyError as error:
        raise _malformed() from error
    if not isinstance(row, Mapping) or any(field not in row or (row[field] is None and field not in nullable) for field in required):
        raise _malformed()
    normalized = {field: row[field] for field in required}
    if shape == "schema_state":
        if "version" not in row or row["version"] is None:
            normalized["version"] = 0
        else:
            normalized["version"] = row["version"]
    if shape == "investigation":
        normalized["selected_sources_json"] = _canonical_source_snapshot(normalized["selected_sources_json"])
    if shape == "query_history":
        normalized["query_plan_json"] = _json_text(normalized["query_plan_json"])
    for field, conversion in conversions.items():
        if normalized[field] is None:
            continue
        normalized[field] = _boolean(normalized[field]) if conversion == "boolean" else _integer(normalized[field])
    rowid = row.get("ROWID")
    if rowid is not None:
        normalized["_catalyst_rowid"] = str(rowid)
    return normalized


def extract_rows(envelope: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if not isinstance(envelope, Mapping) or envelope.get("status") != "success":
        raise _malformed()
    data = envelope.get("data")
    if isinstance(data, list):
        rows = data
    elif isinstance(data, Mapping) and isinstance(data.get("rows"), list):
        rows = data["rows"]
    else:
        raise _malformed()
    if not all(isinstance(row, Mapping) for row in rows):
        raise _malformed()
    return list(rows)
