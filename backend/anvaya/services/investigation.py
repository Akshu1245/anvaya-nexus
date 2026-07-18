from __future__ import annotations

import json
from collections import deque

from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate
from backend.anvaya.services.source_registry import list_sources


PRESETS = {
    "Case Investigation": ["CCTNS_REPLICA", "FORENSICS_REPLICA", "VEHICLE_REPLICA", "CONTEXT_FIXTURE"],
    "Vehicle Verification": ["CCTNS_REPLICA", "VEHICLE_REPLICA"],
    "Forensic Review": ["CCTNS_REPLICA", "FORENSICS_REPLICA"],
    "Custom": [],
}


def source_control(repository, user, purpose):
    permitted = set(evaluate(user, purpose, [], "SOURCE_LIST").permitted_sources)
    sources = []
    for source in list_sources(repository):
        source["synthetic_replica"] = True
        source["permission_state"] = "permitted" if source["id"] in permitted else "denied"
        source["selectable"] = source["id"] in permitted and source["status"] != "Unavailable"
        source["limitation"] = source["description"]
        sources.append(source)
    return {"sources": sources, "presets": PRESETS}


def _record_passport(repository, source_record_id, masking_level):
    row = repository.connection.execute("""SELECT sr.*, ss.name AS source_name, ss.description AS limitations
        FROM source_records sr JOIN source_systems ss ON ss.id=sr.source_system_id WHERE sr.id=?""", (source_record_id,)).fetchone()
    if not row:
        return {"source_record_id": source_record_id, "warning": "No provenance available."}
    payload = json.loads(row["payload_json"])
    transformed = [dict(item) for item in repository.connection.execute("SELECT operation,source_field,target_field,rule_version,occurred_at,outcome FROM transformation_events WHERE source_record_id=? ORDER BY occurred_at", (source_record_id,))]
    # Source payloads may contain direct identifiers. Preserve evidence that a value exists,
    # but never use a passport as a raw-value bypass.
    if masking_level != "NONE":
        payload = {key: ("***masked***" if any(token in key.lower() for token in ("name", "phone", "imei", "vehicle", "address", "evidence")) else value) for key, value in payload.items()}
    result = {"source_record_id": row["id"], "source_system": row["source_name"], "synthetic_external_id": row["external_id"], "version": row["version"], "source_updated_at": row["source_updated_at"], "imported_at": row["imported_at"], "access_class": row["access_class"], "reliability_role": row["reliability_role"], "freshness_state": row["freshness_state"], "checksum": row["checksum"], "original_source_value": payload, "normalized_transformed_value": {"canonical_mapping": True}, "derived_relationship": None, "application_interpretation": "Source-backed factual metadata only.", "transformation_history": transformed, "source_limitations": row["limitations"]}
    return mask_case(result, masking_level)


def passport(repository, user, purpose, source_record_id, station=None, district=None):
    decision = evaluate(user, purpose, [], "SOURCE_PASSPORT", record_station=station, record_district=district)
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    result = _record_passport(repository, source_record_id, decision.masking_level)
    result["masking_state"] = result.pop("masking")
    return result


def case_360(repository, user, purpose, case_id):
    case = repository.connection.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if not case:
        raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    decision = evaluate(user, purpose, ["CCTNS_REPLICA"], "CASE_REVIEW", record_station=case["station_id"], record_district=case["district_id"])
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    edges = [dict(row) for row in repository.connection.execute("SELECT * FROM entity_edges WHERE source_type='CASE' AND source_id=?", (case_id,))]
    entities = []
    tables = {"PERSON": ("persons", "display_name"), "PHONE": ("phones", "synthetic_number"), "DEVICE": ("devices", "synthetic_imei"), "VEHICLE": ("vehicles", "synthetic_registration"), "LOCATION": ("locations", "locality")}
    for edge in edges:
        if edge["target_type"] not in tables: continue
        table, field = tables[edge["target_type"]]
        row = repository.connection.execute(f"SELECT id,{field} AS value,source_record_id FROM {table} WHERE id=?", (edge["target_id"],)).fetchone()
        if row:
            entity = {"type": edge["target_type"], "id": row["id"], "value": row["value"], "source_record_references": [row["source_record_id"], edge["source_record_id"]]}
            entities.append(mask_case({"person_name": entity["value"] if edge["target_type"] == "PERSON" else None, "phone": entity["value"] if edge["target_type"] == "PHONE" else None, "imei": entity["value"] if edge["target_type"] == "DEVICE" else None, "vehicle_registration": entity["value"] if edge["target_type"] == "VEHICLE" else None, **entity}, decision.masking_level))
    evidence = [mask_case({**dict(row), "sensitive_evidence_reference": row["id"], "evidence_status": row["status"]}, decision.masking_level) for row in repository.connection.execute("SELECT * FROM evidence_records WHERE case_id=?", (case_id,))]
    forensics = [dict(row) for row in repository.connection.execute("SELECT * FROM forensic_events WHERE case_id=?", (case_id,))]
    issues = [dict(row) for row in repository.connection.execute("SELECT * FROM trust_issues WHERE case_id=?", (case_id,))]
    overview = mask_case({**dict(case), "jurisdiction_state": "assigned_station" if case["station_id"] == user["assigned_station"] else "external", "source_record_references": [case["source_record_id"]]}, decision.masking_level)
    timeline = [{"kind": "incident", "at": case["incident_at"], "source_record_id": case["source_record_id"]}, {"kind": "registration", "at": case["registered_at"], "source_record_id": case["source_record_id"]}] + [{"kind": row["event_type"], "at": row["occurred_at"], "source_record_id": row["source_record_id"]} for row in forensics]
    return {"overview": overview, "entities": entities, "evidence": evidence, "timeline": timeline, "source_records": [_record_passport(repository, case["source_record_id"], decision.masking_level)], "trust_issues": issues, "warnings": ["Seeded/imported trust issues are displayed; no assurance engine has run."]}


def discover(repository, user, purpose, plan):
    # Candidate discovery: only records a shared source-backed entity; never an identity claim.
    base_filters = plan.filters
    from backend.anvaya.services.search import search_cases
    bases = search_cases(repository, user, purpose, plan)
    output = []
    seen = set()
    for base in bases:
        edge_rows = repository.connection.execute("SELECT * FROM entity_edges WHERE source_type='CASE' AND source_id=?", (base["id"],)).fetchall()
        for edge in edge_rows:
            related = repository.connection.execute("SELECT * FROM entity_edges WHERE target_type=? AND target_id=? AND source_type='CASE' AND source_id<>? LIMIT 25", (edge["target_type"], edge["target_id"], base["id"])).fetchall()
            for link in related:
                candidate = repository.connection.execute("SELECT * FROM cases WHERE id=?", (link["source_id"],)).fetchone()
                if not candidate or candidate["id"] in seen: continue
                decision = evaluate(user, purpose, plan.selected_sources, "DISCOVER", record_station=candidate["station_id"], record_district=candidate["district_id"])
                if not decision.allowed: continue
                seen.add(candidate["id"])
                label = {"PHONE": "shared phone", "DEVICE": "shared IMEI/device", "VEHICLE": "shared vehicle", "LOCATION": "shared location"}.get(edge["target_type"], "source-backed candidate relationship")
                result = mask_case({"id": candidate["id"], "fir_number": candidate["fir_number"], "offence": candidate["offence"], "incident_at": candidate["incident_at"], "status": candidate["status"], "station_id": candidate["station_id"], "district_id": candidate["district_id"], "relationship_reason": label, "relationship_type": edge["relationship_type"], "candidate_relationship": True, "source_record_references": [candidate["source_record_id"], edge["source_record_id"], link["source_record_id"]], "freshness_state": "Fresh", "jurisdiction_state": "assigned_station" if candidate["station_id"] == user["assigned_station"] else "external", "conflicts_limitations": "Candidate relationship only; not identity confirmation."}, decision.masking_level)
                output.append(result)
    return output[:min(plan.result_limit, 25)]


def relationship_path(repository, user, purpose, start_id, end_id, max_hops=3):
    max_hops = max(1, min(int(max_hops), 3))
    rows = [dict(row) for row in repository.connection.execute("SELECT * FROM entity_edges LIMIT 200")]
    graph = {}
    for edge in rows:
        graph.setdefault((edge["source_type"], edge["source_id"]), []).append((edge["target_type"], edge["target_id"], edge))
        graph.setdefault((edge["target_type"], edge["target_id"]), []).append((edge["source_type"], edge["source_id"], edge))
    queue = deque([(("CASE", start_id), [])]); visited = {("CASE", start_id)}
    while queue:
        node, path = queue.popleft()
        if node[1] == end_id: return {"path": path, "source_list": sorted({edge["source_record_reference"] for edge in path}), "limited": False, "max_hops": max_hops}
        if len(path) >= max_hops: continue
        for typ, ident, edge in graph.get(node, []):
            next_node = (typ, ident)
            if next_node not in visited and len(visited) < 20:
                visited.add(next_node); queue.append((next_node, path + [{"from": node, "to": next_node, "relationship_type": edge["relationship_type"], "source_record_reference": edge["source_record_id"]}]))
    return {"path": [], "source_list": [], "limited": True, "max_hops": max_hops, "warning": "No bounded relationship path found."}
