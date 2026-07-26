"""Deterministic, source-backed FIR Record Assurance; no scoring or correction."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate


RULE_VERSION = "fir-assurance-v1"
SEVERITY = {
    "DUPLICATE_CASE_NUMBER_WITHIN_UNIT_YEAR": "BLOCKING", "DUPLICATE_CRIME_NUMBER_WITHIN_UNIT_YEAR": "BLOCKING",
    "INCIDENT_START_AFTER_END": "BLOCKING", "INFORMATION_RECEIVED_AFTER_REGISTRATION": "BLOCKING",
    "COORDINATE_PAIR_INCOMPLETE": "BLOCKING", "ACT_SECTION_MISMATCH": "BLOCKING",
    "UNIT_DISTRICT_MISMATCH": "BLOCKING", "OFFICER_UNIT_MISMATCH": "BLOCKING",
    "ARREST_CASE_MISMATCH": "BLOCKING", "ARREST_WITHOUT_ACCUSED": "BLOCKING", "INVALID_CHARGESHEET_TYPE": "BLOCKING",
    "SOURCE_UNAVAILABLE": "WARNING", "SOURCE_STALE": "INFORMATIONAL", "TRANSFORMATION_HISTORY_MISSING": "WARNING",
    "CASE_WITHOUT_ACCUSED": "INFORMATIONAL", "CASE_WITHOUT_COMPLAINANT": "WARNING", "CASE_WITHOUT_LEGAL_SECTION": "WARNING",
    "BRIEF_FACTS_MISSING": "WARNING", "MISSING_POLICE_UNIT": "WARNING", "MISSING_REGISTERING_OFFICER": "WARNING",
    "MISSING_CASE_CATEGORY": "WARNING", "MISSING_GRAVITY": "WARNING", "MISSING_CRIME_HEAD": "WARNING", "MISSING_CANONICAL_STATUS": "WARNING",
    "INACTIVE_ACT_REFERENCE": "WARNING", "INACTIVE_SECTION_REFERENCE": "WARNING", "INACTIVE_CLASSIFICATION_REFERENCE": "WARNING",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(case, code, category, explanation, *, record_type="CASE", record_id=None, field=None, observed=None, source_ids=()):
    record_id = record_id or case["id"]
    digest = hashlib.sha256(f"{RULE_VERSION}|{code}|{case['id']}|{record_type}|{record_id}|{field or ''}".encode()).hexdigest()[:18].upper()
    return {
        "id": f"FIR-ASSURE-{digest}", "case_id": case["id"], "rule_code": code, "category": category,
        "severity": SEVERITY.get(code, "WARNING"), "description": explanation,
        "affected_record_type": record_type, "affected_record_id": record_id, "affected_field": field,
        "observed_values_json": json.dumps(observed or {}, sort_keys=True),
        "source_record_ids_json": json.dumps(list(dict.fromkeys(source_ids)), sort_keys=True),
        "deterministic_rule_version": RULE_VERSION, "updated_at": _now(),
    }


def _source_ids(rows):
    return tuple(row["source_record_id"] for row in rows if row.get("source_record_id"))


def evaluate_case_assurance(repository, case_id: str) -> list[dict]:
    """Evaluate one bounded case using only fixed canonical reads and staged seeds."""
    case = repository.find_case_360_case(case_id)
    if not case:
        raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    people = repository.list_case_people(case_id, source_system_ids=("CCTNS_REPLICA",))
    legal = repository.list_case_legal_sections(case_id, source_system_ids=("CCTNS_REPLICA",))
    classifications = repository.find_case_classifications(case_id) or {}
    arrests = repository.list_case_arrest_surrender_events(case_id, source_system_ids=("CCTNS_REPLICA",))
    chargesheets = repository.list_case_chargesheets(case_id, source_system_ids=("CCTNS_REPLICA",))
    findings = []
    source_ids = (case["source_record_id"],)
    if not case.get("case_number"): findings.append(_finding(case, "CASE_NUMBER_MISSING", "CaseMaster", "Case Number is not recorded.", field="case_number", source_ids=source_ids))
    if not case.get("crime_number"): findings.append(_finding(case, "CRIME_NUMBER_MISSING", "CaseMaster", "Crime Number is not recorded.", field="crime_number", source_ids=source_ids))
    if case.get("incident_from_at") and case.get("incident_to_at") and case["incident_from_at"] > case["incident_to_at"]: findings.append(_finding(case, "INCIDENT_START_AFTER_END", "CaseMaster", "Incident start is after incident end.", field="incident_from_at", source_ids=source_ids))
    if case.get("information_received_at") and case.get("registered_at") and case["information_received_at"] > case["registered_at"]: findings.append(_finding(case, "INFORMATION_RECEIVED_AFTER_REGISTRATION", "CaseMaster", "Information received time is after FIR registration.", field="information_received_at", source_ids=source_ids))
    if (case.get("latitude") is None) != (case.get("longitude") is None): findings.append(_finding(case, "COORDINATE_PAIR_INCOMPLETE", "CaseMaster", "Only one coordinate is present.", field="coordinates", source_ids=source_ids))
    if not case.get("brief_facts"): findings.append(_finding(case, "BRIEF_FACTS_MISSING", "CaseMaster", "Brief facts are not recorded.", field="brief_facts", source_ids=source_ids))
    roles = {row["role"] for row in people}
    if "COMPLAINANT" not in roles: findings.append(_finding(case, "CASE_WITHOUT_COMPLAINANT", "People and roles", "No complainant role is linked to this FIR.", source_ids=source_ids))
    if "ACCUSED" not in roles: findings.append(_finding(case, "CASE_WITHOUT_ACCUSED", "People and roles", "No accused role is currently linked; this is informational only.", source_ids=source_ids))
    if not legal: findings.append(_finding(case, "CASE_WITHOUT_LEGAL_SECTION", "Legal and classification", "No Act and Section association is recorded.", source_ids=source_ids))
    for row in legal:
        if row["act_id"] != row.get("section_act_id", row["act_id"]): findings.append(_finding(case, "ACT_SECTION_MISMATCH", "Legal and classification", "The linked Section belongs to a different Act.", record_type="CASE_LEGAL_SECTION", record_id=row["id"], source_ids=_source_ids([row])))
        if not row.get("act_active", 1): findings.append(_finding(case, "INACTIVE_ACT_REFERENCE", "Legal and classification", "An inactive Act remains linked to this FIR.", record_type="LEGAL_ACT", record_id=row["act_id"], source_ids=_source_ids([row])))
        if not row.get("section_active", 1): findings.append(_finding(case, "INACTIVE_SECTION_REFERENCE", "Legal and classification", "An inactive Section remains linked to this FIR.", record_type="LEGAL_SECTION", record_id=row["section_id"], source_ids=_source_ids([row])))
    for field, code in (("case_category", "MISSING_CASE_CATEGORY"), ("gravity_offence", "MISSING_GRAVITY"), ("crime_major_head", "MISSING_CRIME_HEAD"), ("canonical_status", "MISSING_CANONICAL_STATUS")):
        if not classifications.get(field): findings.append(_finding(case, code, "Legal and classification", f"{field.replace('_', ' ').title()} is not recorded.", field=field, source_ids=source_ids))
    if not case.get("police_unit_id"): findings.append(_finding(case, "MISSING_POLICE_UNIT", "Organisation and court", "Police unit is not recorded.", field="police_unit_id", source_ids=source_ids))
    if not case.get("registering_officer_id"): findings.append(_finding(case, "MISSING_REGISTERING_OFFICER", "Organisation and court", "Registering officer is not recorded.", field="registering_officer_id", source_ids=source_ids))
    for arrest in arrests:
        accused = repository.list_arrest_event_accused(arrest["id"], source_system_ids=("CCTNS_REPLICA",))
        if not accused: findings.append(_finding(case, "ARREST_WITHOUT_ACCUSED", "Arrest and surrender", "Arrest or surrender event has no linked accused.", record_type="ARREST_EVENT", record_id=arrest["id"], source_ids=_source_ids([arrest])))
        if arrest["event_at"] < (case.get("incident_from_at") or case["incident_at"]): findings.append(_finding(case, "ARREST_BEFORE_INCIDENT", "Arrest and surrender", "Arrest or surrender is dated before the incident.", record_type="ARREST_EVENT", record_id=arrest["id"], source_ids=_source_ids([arrest])))
    for sheet in chargesheets:
        if sheet["report_type"] not in {"A_CHARGESHEET", "B_FALSE", "C_UNDETECTED"}: findings.append(_finding(case, "INVALID_CHARGESHEET_TYPE", "Chargesheets", "Final-report type is not allowlisted.", record_type="CHARGESHEET", record_id=sheet["id"], source_ids=_source_ids([sheet])))
        if sheet["filed_at"] < case["registered_at"]: findings.append(_finding(case, "CHARGESHEET_BEFORE_REGISTRATION", "Chargesheets", "Chargesheet is dated before FIR registration.", record_type="CHARGESHEET", record_id=sheet["id"], source_ids=_source_ids([sheet])))
    source = repository.find_source_passport_record(case["source_record_id"])
    if not source: findings.append(_finding(case, "SOURCE_RECORD_MISSING", "Provenance", "Primary source record is unavailable.", source_ids=source_ids))
    elif source["freshness_state"] == "Unavailable": findings.append(_finding(case, "SOURCE_UNAVAILABLE", "Provenance", "Primary source is unavailable.", source_ids=source_ids))
    elif source["freshness_state"] == "Stale": findings.append(_finding(case, "SOURCE_STALE", "Provenance", "Primary source is stale but remains available.", source_ids=source_ids))
    elif not repository.list_source_transformations(case["source_record_id"]): findings.append(_finding(case, "TRANSFORMATION_HISTORY_MISSING", "Provenance", "Primary source has no transformation history.", source_ids=source_ids))
    # Preserve seeded/rejected defects as factual staged assurance inputs.
    for seed in repository.list_case_materialized_trust_issues(case_id):
        if seed.get("deterministic_rule_version"):
            continue
        code = {"duplicate_identifier": "DUPLICATE_CRIME_NUMBER_WITHIN_UNIT_YEAR", "invalid_chronology": "INCIDENT_START_AFTER_END", "missing_source": "SOURCE_RECORD_MISSING"}.get(seed["issue_type"], "STAGED_SOURCE_DEFECT")
        findings.append(_finding(case, code, "Staged source defect", "A rejected or staged synthetic source defect requires review; canonical FIR data was not altered.", record_type="STAGED_SOURCE_RECORD", record_id=seed["id"], source_ids=tuple(json.loads(seed["source_record_ids_json"]))))
    materialized = [repository.upsert_trust_issue(item) for item in findings]
    return materialized


def list_case_assurance(repository, user, purpose, case_id, selected_sources, status=None):
    case = repository.find_case_360_case(case_id)
    if not case: raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    decision = evaluate(user, purpose, selected_sources, "CASE_REVIEW", record_station=case["station_id"], record_district=case["district_id"])
    if not decision.allowed: raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    evaluate_case_assurance(repository, case_id)
    rows = repository.list_case_materialized_trust_issues(case_id)
    shaped = []
    for row in rows[:100]:
        if status and row["status"] != status: continue
        observed = json.loads(row.get("observed_values_json") or "{}")
        shaped.append({"id": row["id"], "rule_code": row.get("rule_code") or f"SEEDED_{row['issue_type'].upper()}", "category": row.get("category") or "Legacy staged issue", "title": (row.get("rule_code") or row["issue_type"]).replace("_", " ").title(), "severity": row["severity"] if row["severity"] in {"BLOCKING", "WARNING", "INFORMATIONAL"} else "WARNING", "status": row["status"], "case_id": row["case_id"], "affected_record_type": row.get("affected_record_type") or "CASE", "affected_record_id": row.get("affected_record_id") or case_id, "affected_field": row.get("affected_field"), "factual_explanation": row["description"], "observed_values": mask_case(observed, decision.masking_level), "source_record_ids": json.loads(row["source_record_ids_json"]), "deterministic_rule_version": row.get("deterministic_rule_version") or "legacy-seed", "acknowledged_at": row.get("acknowledged_at"), "resolved_at": row.get("resolved_at"), "resolution_note": row.get("resolution_note")})
    shaped.sort(key=lambda item: ({"BLOCKING": 0, "WARNING": 1, "INFORMATIONAL": 2}[item["severity"]], item["category"], item["rule_code"], item["id"]))
    counts = {key: sum(item["severity"] == key for item in shaped) for key in ("BLOCKING", "WARNING", "INFORMATIONAL")}
    counts.update({key: sum(item["status"] == key for item in shaped) for key in ("OPEN", "ACKNOWLEDGED", "RESOLVED")})
    return {"case_id": case_id, "rule_version": RULE_VERSION, "findings": shaped, "summary": counts, "selected_sources": list(dict.fromkeys(selected_sources))}


def set_assurance_status(repository, user, purpose, case_id, finding_id, status, note):
    if user["role"] != "SUPERVISOR": raise ApiError("ASSURANCE_ACTION_DENIED", "Only Supervisors may update Record Assurance findings.", 403)
    row = repository.update_trust_issue_status(finding_id, status, note, user["id"], _now())
    if not row or row["case_id"] != case_id: raise ApiError("ASSURANCE_FINDING_NOT_FOUND", "Record Assurance finding was not found.", 404)
    return row
