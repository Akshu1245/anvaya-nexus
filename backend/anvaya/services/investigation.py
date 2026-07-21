from __future__ import annotations

from collections import deque

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.discovery_requests import DiscoveryRequest, RelationshipPathRequest
from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate
from backend.anvaya.services.source_registry import list_sources
from backend.anvaya.services.assurance import list_case_assurance


PRESETS = {
    "Case Investigation": ["CCTNS_REPLICA", "FORENSICS_REPLICA", "VEHICLE_REPLICA", "CONTEXT_FIXTURE"],
    "Vehicle Verification": ["CCTNS_REPLICA", "VEHICLE_REPLICA"],
    "Forensic Review": ["CCTNS_REPLICA", "FORENSICS_REPLICA"],
    "Custom": [],
}


CASE_360_SECTION_ORDER = (
    ("fir_summary", "FIR Summary"),
    ("incident", "Incident"),
    ("people", "People"),
    ("statements", "Statements"),
    ("legal", "Acts & Sections"),
    ("classifications", "Classification"),
    ("organisation", "Police & Court"),
    ("arrests", "Arrest / Surrender"),
    ("chargesheets", "Chargesheet / Final Report"),
    ("property_identifiers", "Property Identifiers"),
    ("evidence", "Evidence"),
    ("exhibits", "Synthetic Exhibits"),
    ("timeline", "Timeline"),
    ("sources", "Sources & Provenance"),
    ("data_quality", "Data Quality"),
)


RELATED_REASON_DETAILS = {
    "SHARED_ACCUSED": ("Shared People", "Shared accused", "DIRECT_SHARED_RECORD", 1),
    "SHARED_ARREST_ACCUSED": ("Shared People", "Shared arrest-linked accused", "DIRECT_SHARED_RECORD", 2),
    "SHARED_COMPLAINANT": ("Shared People", "Shared complainant", "DIRECT_SHARED_RECORD", 3),
    "SHARED_VICTIM": ("Shared People", "Shared victim", "DIRECT_SHARED_RECORD", 4),
    "SHARED_ACT_SECTION": ("Shared Legal Provisions", "Shared Act and Section", "DIRECT_SHARED_RECORD", 5),
    "SHARED_POLICE_UNIT": ("Shared Organisation", "Shared police unit", "DIRECT_SHARED_RECORD", 6),
    "SHARED_COURT": ("Shared Organisation", "Shared court", "DIRECT_SHARED_RECORD", 7),
    "SHARED_REGISTERING_OFFICER": ("Shared Organisation", "Shared registering officer", "DIRECT_SHARED_RECORD", 8),
    "SHARED_CRIME_MINOR_HEAD": ("Shared Classification", "Shared minor crime sub-head", "SHARED_CLASSIFICATION", 9),
    "SHARED_CRIME_MAJOR_HEAD": ("Shared Classification", "Shared major crime head", "SHARED_CLASSIFICATION", 10),
    "SHARED_CASE_CATEGORY": ("Shared Classification", "Shared case category", "SHARED_CLASSIFICATION", 11),
    "SHARED_GRAVITY": ("Shared Classification", "Shared gravity", "SHARED_CLASSIFICATION", 11),
    "SHARED_CANONICAL_STATUS": ("Shared Classification", "Shared canonical status", "SHARED_CLASSIFICATION", 11),
    "TEMPORAL_OVERLAP": ("Temporal Context", "Incident dates overlap or are within 7 days", "TEMPORAL_OVERLAP", 12),
}


def source_control(repository, user, purpose):
    decision = evaluate(user, purpose, [], "SOURCE_LIST")
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    permitted = set(decision.permitted_sources)
    sources = []
    for source in list_sources(repository):
        source["synthetic_replica"] = True
        source["permission_state"] = "permitted" if source["id"] in permitted else "denied"
        source["selectable"] = source["id"] in permitted and source["status"] != "Unavailable"
        source["limitation"] = source["description"]
        sources.append(source)
    return {"sources": sources, "presets": PRESETS}


def _record_passport(repository, source_record_id, masking_level):
    row = repository.find_source_passport_record(source_record_id)
    if not row:
        return {"source_record_id": source_record_id, "warning": "No provenance available."}
    transformed = repository.list_source_transformations(source_record_id)
    # A passport establishes source provenance, not a raw-value bypass. Payloads,
    # checksums, and external identifiers remain storage-only values.
    result = {"source_record_id": row["id"], "source_system": row["source_name"], "version": row["version"], "source_updated_at": row["source_updated_at"], "imported_at": row["imported_at"], "access_class": row["access_class"], "reliability_role": row["reliability_role"], "freshness_state": row["freshness_state"], "normalized_transformed_value": {"canonical_mapping": True}, "derived_relationship": None, "application_interpretation": "Source-backed factual metadata only.", "transformation_history": transformed, "source_limitations": row["limitations"]}
    return mask_case(result, masking_level)


def _case_source_summary(repository, source_record_id):
    """Return provenance safe for the Case 360 view, never the source payload."""
    row = repository.find_source_passport_record(source_record_id)
    if not row:
        return {"source_record_id": source_record_id, "available": False, "warning": "No provenance available."}
    return {
        "source_record_id": row["id"],
        "available": True,
        "source_system": row["source_name"],
        "version": row["version"],
        "source_updated_at": row["source_updated_at"],
        "imported_at": row["imported_at"],
        "access_class": row["access_class"],
        "reliability_role": row["reliability_role"],
        "freshness_state": row["freshness_state"],
        "source_limitations": row["limitations"],
        "transformation_history": repository.list_source_transformations(source_record_id),
    }


def passport(repository, user, purpose, source_record_id, station=None, district=None):
    decision = evaluate(user, purpose, [], "SOURCE_PASSPORT", record_station=station, record_district=district)
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    result = _record_passport(repository, source_record_id, decision.masking_level)
    result["masking_state"] = result.pop("masking", {"applied": False, "level": decision.masking_level, "fields": []})
    return result


def case_360(repository, user, purpose, case_id):
    case = repository.find_case_360_case(case_id)
    if not case:
        raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    decision = evaluate(user, purpose, ["CCTNS_REPLICA"], "CASE_REVIEW", record_station=case["station_id"], record_district=case["district_id"])
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    # Legacy generic entity links remain in their compatibility-only routes.
    # The primary FIR Case 360 contract deliberately carries no demographic
    # or legacy identifier values.
    evidence = [mask_case({**row, "sensitive_evidence_reference": row["id"], "evidence_status": row["status"]}, decision.masking_level) for row in repository.list_case_360_evidence(case_id)]
    documents = [mask_case(dict(row), decision.masking_level) for row in repository.list_case_360_documents(case_id)]
    exhibits = []
    for row in repository.list_case_360_exhibits(case_id, include_blob=False):
        custody = []
        if hasattr(repository, "list_exhibit_custody_events"):
            try:
                custody = repository.list_exhibit_custody_events(row["id"])
            except Exception:
                custody = []
        masked = mask_case({
            "id": row["id"], "exhibit_code": row["exhibit_code"], "filename": row["filename"],
            "mime_type": row["mime_type"], "sha256": row["sha256"], "byte_size": row["byte_size"],
            "collected_at": row["collected_at"], "collected_by_ref": row.get("collected_by_ref"),
            "chain_status": row["chain_status"], "caption": row["caption"], "sensitivity": row["sensitivity"],
            "source_record_id": row["source_record_id"], "evidence_id": row.get("evidence_id"),
            "exhibit_kind": row.get("exhibit_kind"),
            "custody_events": custody,
            "synthetic_exhibit": True, "not_operational_evidence": True,
        }, decision.masking_level)
        exhibits.append(masked)
    property_identifiers = []
    for row in repository.list_case_360_entities(case_id):
        if row["target_type"] not in {"PHONE", "DEVICE", "VEHICLE"}:
            continue
        field = {"PHONE": "phone", "DEVICE": "imei", "VEHICLE": "vehicle_registration"}[row["target_type"]]
        masked = mask_case({field: row["value"], "target_type": row["target_type"], "target_id": row["target_id"], "source_record_id": row.get("entity_source_record_id") or row.get("edge_source_record_id")}, decision.masking_level)
        property_identifiers.append({
            "type": row["target_type"], "target_id": row["target_id"], "value": masked.get(field),
            "source_record_id": masked.get("source_record_id"), "masking": masked["masking"],
        })
    forensics = repository.list_case_360_forensics(case_id)
    assurance = list_case_assurance(repository, user, purpose, case_id, ("CCTNS_REPLICA",))
    issues = assurance["findings"]
    legal = repository.list_case_legal_sections(case_id, source_system_ids=("CCTNS_REPLICA",))
    classifications = repository.find_case_classifications(case_id)
    arrest_rows = repository.list_case_arrest_surrender_events(case_id, source_system_ids=("CCTNS_REPLICA",))
    arrests = []
    for event in arrest_rows:
        linked_accused = []
        for link in repository.list_arrest_event_accused(event["id"], source_system_ids=("CCTNS_REPLICA",)):
            masked = mask_case({"person_name": link["display_name"]}, decision.masking_level)
            linked_accused.append({
                "person_id": link["person_id"], "display_name": masked.pop("person_name"),
                "role": link["role"], "role_sequence": link["role_sequence"], "sequence": link["sequence"],
                "source_record_id": link["source_record_id"], "masking": masked["masking"],
            })
        arrests.append({
            "id": event["id"], "event_type": event["event_type"], "event_at": event["event_at"],
            "state_code": event["state_code"], "district_code": event["district_code"],
            "police_unit_code": event["police_unit_code"], "investigating_officer_ref": event["investigating_officer_ref"],
            "court_ref": event["court_ref"], "remarks": event["remarks"], "source_record_id": event["source_record_id"],
            "state_id": event.get("state_id"), "district_id": event.get("district_id"), "police_unit_id": event.get("police_unit_id"),
            "investigating_officer_id": event.get("investigating_officer_id"), "court_id": event.get("court_id"),
            "accused": linked_accused,
        })
    chargesheets = repository.list_case_chargesheets(case_id, source_system_ids=("CCTNS_REPLICA",))
    organisation = repository.find_case_organisation(case_id)
    if organisation:
        officer_mask = mask_case({"person_name": organisation.get("officer_name")}, decision.masking_level)
        organisation["officer_name"] = officer_mask.pop("person_name")
        organisation["masking"] = officer_mask["masking"]
        if organisation.get("investigating_officer_name"):
            io_mask = mask_case({"person_name": organisation.get("investigating_officer_name")}, decision.masking_level)
            organisation["investigating_officer_name"] = io_mask.pop("person_name")
            organisation["investigating_officer_masking"] = io_mask["masking"]
        organisation["investigating_officer"] = {
            "id": organisation.get("investigating_officer_id"),
            "display_name": organisation.get("investigating_officer_name"),
            "employee_code": organisation.get("investigating_employee_code"),
            "rank_name": organisation.get("investigating_rank_name"),
        } if organisation.get("investigating_officer_id") else None
    for event in arrests:
        event["organisation"] = {
            "state": repository.find_state(event.get("state_id")) if event.get("state_id") else None,
            "district": repository.find_district(event.get("district_id")) if event.get("district_id") else None,
            "police_unit": repository.find_police_unit(event.get("police_unit_id")) if event.get("police_unit_id") else None,
            "investigating_officer": repository.find_police_employee(event.get("investigating_officer_id")) if event.get("investigating_officer_id") else None,
            "court": repository.find_court(event.get("court_id")) if event.get("court_id") else None,
        }
        if event["organisation"]["investigating_officer"]:
            masked = mask_case({"person_name": event["organisation"]["investigating_officer"]["display_name"]}, decision.masking_level)
            event["organisation"]["investigating_officer"]["display_name"] = masked.pop("person_name")
    for row in chargesheets:
        row["filing_officer"] = repository.find_police_employee(row.get("filing_officer_id")) if row.get("filing_officer_id") else None
        if row["filing_officer"]:
            masked = mask_case({"person_name": row["filing_officer"]["display_name"]}, decision.masking_level)
            row["filing_officer"]["display_name"] = masked.pop("person_name")
    people = {"complainants": [], "victims": [], "accused": [], "witnesses": []}
    for row in repository.list_case_people(case_id, source_system_ids=("CCTNS_REPLICA",)):
        masked = mask_case({"person_name": row["display_name"]}, decision.masking_level)
        section = {"COMPLAINANT": "complainants", "VICTIM": "victims", "ACCUSED": "accused", "WITNESS": "witnesses"}.get(row["role"])
        if not section:
            continue
        people[section].append({
            "person_id": row["person_id"],
            "display_name": masked.pop("person_name"),
            "role": row["role"],
            "role_sequence": row["role_sequence"],
            "source_record_id": row["source_record_id"],
            "masking": masked["masking"],
        })
    statements = []
    if hasattr(repository, "list_case_person_statements"):
        try:
            for row in repository.list_case_person_statements(case_id):
                masked = mask_case({"body_text": row.get("body_text"), "person_name": row.get("display_name")}, decision.masking_level)
                statements.append({
                    "id": row["id"],
                    "person_id": row.get("person_id"),
                    "display_name": masked.get("person_name"),
                    "statement_type": row.get("statement_type"),
                    "body_text": masked.get("body_text"),
                    "recorded_at": row.get("recorded_at"),
                    "language_code": row.get("language_code"),
                    "role": row.get("role"),
                    "source_record_id": row.get("source_record_id"),
                    "masking": masked.get("masking"),
                })
        except Exception:
            statements = []
    overview = mask_case({**case, "jurisdiction_state": "assigned_station" if case["station_id"] == user["assigned_station"] else "external", "source_record_references": [case["source_record_id"]]}, decision.masking_level)
    coordinates_visible = decision.masking_level == "NONE"
    incident = {
        "incident_from_at": case.get("incident_from_at") or case.get("incident_at"),
        "incident_to_at": case.get("incident_to_at"),
        "information_received_at": case.get("information_received_at"),
        "legacy_incident_at": case.get("incident_at"),
        "latitude": case.get("latitude") if coordinates_visible else None,
        "longitude": case.get("longitude") if coordinates_visible else None,
        "coordinates_masked": bool(not coordinates_visible and (case.get("latitude") is not None or case.get("longitude") is not None)),
        "brief_facts": case.get("brief_facts") if coordinates_visible else "Masked by policy.",
        "brief_facts_masked": bool(not coordinates_visible and case.get("brief_facts")),
        "source_record_id": case["source_record_id"],
    }
    fir_summary = {
        "id": overview["id"], "crime_number": overview.get("crime_number"), "case_number": overview.get("case_number"),
        "fir_number": overview.get("fir_number"), "canonical_status": classifications.get("canonical_status") if classifications else None,
        "legacy_status": overview.get("status"), "registered_at": overview.get("registered_at"), "source_record_id": case["source_record_id"],
    }
    timeline = [
        {"id": "INCIDENT_START", "kind": "INCIDENT_START", "label": "Incident start", "at": case.get("incident_from_at") or case["incident_at"], "source_record_id": case["source_record_id"]},
        *([{ "id":"INCIDENT_END", "kind":"INCIDENT_END", "label":"Incident end", "at":case["incident_to_at"], "source_record_id":case["source_record_id"]}] if case.get("incident_to_at") and case.get("incident_to_at") != (case.get("incident_from_at") or case["incident_at"]) else []),
        *([{ "id":"INFORMATION_RECEIVED", "kind":"INFORMATION_RECEIVED", "label":"Information received", "at":case["information_received_at"], "source_record_id":case["source_record_id"]}] if case.get("information_received_at") else []),
        {"id": "FIR_REGISTERED", "kind": "FIR_REGISTERED", "label": "FIR registered", "at": case["registered_at"], "source_record_id": case["source_record_id"]},
        *[{"id": row["id"], "kind": row["event_type"], "label": row["event_type"], "at": row["occurred_at"], "source_record_id": row["source_record_id"]} for row in forensics],
        *[{"id": row["id"], "kind": row["event_type"], "label": row["event_type"], "at": row["event_at"], "source_record_id": row["source_record_id"]} for row in arrests],
        *[{"id": row["id"], "kind": "CHARGESHEET_FILED" if row["report_type"] == "A_CHARGESHEET" else row["report_type"] + "_REPORT", "label": row["report_type"], "at": row["filed_at"], "source_record_id": row["source_record_id"]} for row in chargesheets],
    ]
    timeline.sort(key=lambda item: (item["at"], item["kind"], item["id"]))
    source_ids = [case["source_record_id"]]
    for group in people.values():
        for person in group:
            if person.get("source_record_id"):
                source_ids.append(person["source_record_id"])
    for link in legal:
        if link.get("source_record_id"):
            source_ids.append(link["source_record_id"])
    for event in arrests:
        if event.get("source_record_id"):
            source_ids.append(event["source_record_id"])
    for row in chargesheets:
        if row.get("source_record_id"):
            source_ids.append(row["source_record_id"])
    for exh in exhibits:
        if exh.get("source_record_id"):
            source_ids.append(exh["source_record_id"])
        for custody in exh.get("custody_events") or []:
            if custody.get("source_record_id"):
                source_ids.append(custody["source_record_id"])
    for statement in statements:
        if statement.get("source_record_id"):
            source_ids.append(statement["source_record_id"])
    sources = [_case_source_summary(repository, source_id) for source_id in dict.fromkeys(source_ids) if source_id]
    return {"sections": [{"id": section_id, "label": label} for section_id, label in CASE_360_SECTION_ORDER], "case": fir_summary, "incident": incident, "people": people, "statements": statements, "legal_provisions": {"associations": legal}, "classification": classifications, "police_and_court": organisation, "arrest_section": {"events": arrests}, "chargesheet_section": {"records": chargesheets}, "property_identifiers": property_identifiers, "evidence_section": {"records": evidence, "forensic_events": forensics, "documents": documents, "exhibits": exhibits}, "data_quality": issues, "assurance": assurance, "sources": sources, "overview": overview, "organisation": organisation, "legacy_compatibility": {"generic_entity_routes": "Compatibility-only; not included in the FIR response."}, "legal": legal, "classifications": classifications, "arrests": arrests, "chargesheets": chargesheets, "evidence": evidence, "documents": documents, "exhibits": exhibits, "timeline": timeline, "source_records": sources, "trust_issues": issues, "warnings": ["Record Assurance uses deterministic source-backed checks; it never alters FIR records.", "Synthetic exhibit images are watermarked placeholders and are not operational evidence.", "Case diary, mahazar detail, remand/bail chronology and court-hearing annexures are not represented in authorised synthetic records."]}


def related_cases(repository, user, purpose, case_id, source_system_ids, limit=10):
    """Explain only stored factual connections; never infer identity or culpability."""
    if not 1 <= limit <= 25:
        raise ApiError("RELATED_CASE_LIMIT_INVALID", "Related case limit must be between 1 and 25.", 400, False)
    base = repository.find_case_360_case(case_id)
    if not base:
        raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    base_decision = evaluate(user, purpose, source_system_ids, "DISCOVER", limit, base["station_id"], base["district_id"])
    if not base_decision.allowed:
        raise ApiError(base_decision.denial_code or "POLICY_DENIED", base_decision.explanation, 403)
    grouped = {}
    for fact in repository.list_related_case_facts(case_id, tuple(dict.fromkeys(source_system_ids)), 25):
        decision = evaluate(user, purpose, source_system_ids, "DISCOVER", limit, fact["station_id"], fact["district_id"])
        if not decision.allowed:
            continue
        group, label, confidence_class, rank = RELATED_REASON_DETAILS[fact["reason_type"]]
        display_value = fact.get("matched_value")
        if group == "Shared People":
            display_value = mask_case({"person_name": display_value}, decision.masking_level).get("person_name")
        reason = {
            "reason_type": fact["reason_type"], "group": group, "label": label,
            "matched_record_id": fact.get("matched_record_id"), "factual_value": display_value,
            "source_record_id": fact["reason_source_record_id"], "source_system_id": fact["source_system_id"],
            "confidence_class": confidence_class,
        }
        candidate = grouped.setdefault(fact["candidate_id"], {"facts": [], "row": fact, "decision": decision, "rank": rank})
        candidate["rank"] = min(candidate["rank"], rank)
        if (reason["reason_type"], reason["matched_record_id"]) not in {(item["reason_type"], item["matched_record_id"]) for item in candidate["facts"]}:
            candidate["facts"].append(reason)
    results = []
    for candidate_id, value in grouped.items():
        row, decision = value["row"], value["decision"]
        summary = {
            "case_id": candidate_id, "crime_number": row["crime_number"], "case_number": row["case_number"],
            "fir_number": row["fir_number"], "registered_at": row["registered_at"],
            "incident_from_at": row["incident_from_at"], "legacy_status": row["status"],
            "source_system_id": row["source_system_id"], "freshness_state": row["freshness_state"],
            "access_class": row["access_class"], "source_record_references": [row["source_record_id"]],
            "jurisdiction_state": "assigned_station" if row["station_id"] == user["assigned_station"] else ("assigned_district" if row["district_id"] == user["assigned_district"] else "external"),
        }
        summary = mask_case({**summary, "person_name": None, "address": None}, decision.masking_level)
        reasons = sorted(value["facts"], key=lambda item: (RELATED_REASON_DETAILS[item["reason_type"]][3], item["label"], str(item["matched_record_id"])))
        direct = sum(item["confidence_class"] == "DIRECT_SHARED_RECORD" for item in reasons)
        classifications = sum(item["confidence_class"] == "SHARED_CLASSIFICATION" for item in reasons)
        temporal = sum(item["confidence_class"] == "TEMPORAL_OVERLAP" for item in reasons)
        results.append({**summary, "related_reasons": reasons, "direct_reason_count": direct, "classification_reason_count": classifications, "temporal_reason_count": temporal, "_rank": value["rank"], "_reason_count": len(reasons)})
    results.sort(key=lambda item: item["case_id"])
    results.sort(key=lambda item: item["registered_at"] or "", reverse=True)
    results.sort(key=lambda item: item["_reason_count"], reverse=True)
    results.sort(key=lambda item: item["direct_reason_count"], reverse=True)
    results.sort(key=lambda item: item["_rank"])
    for result in results:
        result.pop("_rank"); result.pop("_reason_count")
    return {
        "base_case": {"case_id": base["id"], "crime_number": base.get("crime_number"), "case_number": base.get("case_number"), "fir_number": base.get("fir_number")},
        "related_cases": results[:limit],
        "metadata": {"selected_sources": list(dict.fromkeys(source_system_ids)), "maximum_results": limit, "ordering": "Fixed factual reason precedence, direct reason count, total reason count, registered date, and case ID.", "temporal_rule": "Incident dates overlap or their starts are within 7 days.", "limitations": "Stored factual relationships only; a connection does not imply guilt, identity, common offender, or recommendation."},
    }


def fir_relationship_graph(repository, user, purpose, case_id, source_system_ids, related_limit=10):
    """Build a bounded FIR relationship view from stored records and D-7 facts."""
    detail = case_360(repository, user, purpose, case_id)
    max_nodes, max_edges = 75, 150
    nodes, edges, node_ids, edge_ids = [], [], set(), set()
    truncated = False

    def add_node(node_id, node_type, label, source_ids=(), secondary_label=None, metadata=None, masked=False):
        nonlocal truncated
        key = f"{node_type}:{node_id}"
        if key in node_ids:
            return True
        if len(nodes) >= max_nodes:
            truncated = True; return False
        node_ids.add(key); nodes.append({"id": node_id, "type": node_type, "label": label, "secondary_label": secondary_label, "status": "AVAILABLE", "masked": masked, "source_record_ids": list(dict.fromkeys(source_ids)), "metadata": metadata or {}})
        return True

    def add_edge(source, target, relation, source_record_id, *, projected=False, factual_basis="Stored FIR record"):
        nonlocal truncated
        edge_id = f"FIR-EDGE-{relation}-{source}-{target}-{source_record_id or 'NONE'}"
        if edge_id in edge_ids:
            return
        if len(edges) >= max_edges:
            truncated = True; return
        edge_ids.add(edge_id)
        source_row = repository.find_source_passport_record(source_record_id) if source_record_id else None
        edges.append({"id": edge_id, "source": source, "target": target, "relationship_type": relation, "label": relation.replace("_", " ").title(), "source_record_id": source_record_id, "source_system": source_row["source_name"] if source_row else "Unavailable source", "freshness": source_row["freshness_state"] if source_row else "Unavailable", "access_class": source_row["access_class"] if source_row else "Unknown", "projected": projected, "factual_basis": factual_basis})

    case_node = detail["case"]
    add_node(case_id, "CASE", f"{case_node.get('crime_number') or case_node.get('fir_number')} · {case_node.get('case_number') or ''}".strip(), [case_node["source_record_id"]], secondary_label=case_node.get("legacy_status"))
    for group, edge_type in (("complainants", "CASE_HAS_COMPLAINANT"), ("victims", "CASE_HAS_VICTIM"), ("accused", "CASE_HAS_ACCUSED")):
        for person in detail["people"][group]:
            add_node(person["person_id"], "PERSON", person["display_name"], [person["source_record_id"]], secondary_label=person["role"], metadata={"roles": [person["role"]]}, masked=person["masking"]["applied"])
            add_edge(case_id, person["person_id"], edge_type, person["source_record_id"])
    for link in detail["legal_provisions"]["associations"]:
        act_id, section_id = link["act_id"], link["section_id"]
        add_node(act_id, "ACT", link["short_name"] or link["act_code"], [link["act_source_record_id"]])
        add_node(section_id, "SECTION", f"Section {link['section_code']}", [link["section_source_record_id"]], secondary_label=link["section_description"])
        add_edge(case_id, act_id, "CASE_INVOKES_ACT", link["source_record_id"])
        add_edge(case_id, section_id, "CASE_INVOKES_SECTION", link["source_record_id"])
        add_edge(section_id, act_id, "SECTION_BELONGS_TO_ACT", link["source_record_id"])
    organisation = detail.get("police_and_court") or {}
    source_id = case_node["source_record_id"]
    if organisation.get("police_unit_id"):
        add_node(organisation["police_unit_id"], "POLICE_UNIT", organisation.get("unit_name") or "Police unit", [source_id]); add_edge(case_id, organisation["police_unit_id"], "CASE_REGISTERED_AT_UNIT", source_id)
    if organisation.get("registering_officer_id"):
        add_node(organisation["registering_officer_id"], "POLICE_OFFICER", organisation.get("officer_name") or "Masked officer", [source_id], secondary_label=organisation.get("designation_name"), masked=bool(organisation.get("masking", {}).get("applied"))); add_edge(case_id, organisation["registering_officer_id"], "CASE_REGISTERED_BY_OFFICER", source_id)
        if organisation.get("police_unit_id"): add_edge(organisation["registering_officer_id"], organisation["police_unit_id"], "OFFICER_ASSIGNED_TO_UNIT", source_id)
    if organisation.get("court_id"):
        add_node(organisation["court_id"], "COURT", organisation.get("court_name") or "Court", [source_id]); add_edge(case_id, organisation["court_id"], "CASE_HEARD_AT_COURT", source_id)
    if organisation.get("canonical_district_id"):
        add_node(organisation["canonical_district_id"], "DISTRICT", organisation.get("district_name") or "District", [source_id])
        if organisation.get("police_unit_id"): add_edge(organisation["police_unit_id"], organisation["canonical_district_id"], "UNIT_BELONGS_TO_DISTRICT", source_id)
    if organisation.get("state_id"):
        add_node(organisation["state_id"], "STATE", organisation.get("state_name") or "State", [source_id])
        if organisation.get("canonical_district_id"): add_edge(organisation["canonical_district_id"], organisation["state_id"], "DISTRICT_BELONGS_TO_STATE", source_id)
    for event in detail["arrest_section"]["events"]:
        add_node(event["id"], "ARREST_EVENT", f"{event['event_type'].title()} · {event['event_at']}", [event["source_record_id"]]); add_edge(case_id, event["id"], "CASE_HAS_ARREST_EVENT", event["source_record_id"])
        for person in event["accused"]:
            add_node(person["person_id"], "PERSON", person["display_name"], [person["source_record_id"]], secondary_label="ACCUSED", masked=person["masking"]["applied"]); add_edge(event["id"], person["person_id"], "ARREST_INVOLVES_ACCUSED", person["source_record_id"])
    for row in detail["chargesheet_section"]["records"]:
        label = {"A_CHARGESHEET": "A Chargesheet", "B_FALSE": "B Report – False", "C_UNDETECTED": "C Report – Undetected"}[row["report_type"]]
        add_node(row["id"], "CHARGESHEET", label, [row["source_record_id"]], secondary_label=row["filed_at"]); add_edge(case_id, row["id"], "CASE_HAS_CHARGESHEET", row["source_record_id"])
    for row in detail["evidence_section"]["records"]:
        typ = "DOCUMENT" if str(row.get("evidence_type", "")).upper() == "DOCUMENT" else "EVIDENCE"
        add_node(row["id"], typ, row.get("description") or row.get("reference") or row["id"], [row["source_record_id"]]); add_edge(case_id, row["id"], "CASE_HAS_DOCUMENT" if typ == "DOCUMENT" else "CASE_HAS_EVIDENCE", row["source_record_id"])
    for row in detail["evidence_section"]["forensic_events"]:
        add_node(row["id"], "FORENSIC_EVENT", row.get("event_type") or row["id"], [row["source_record_id"]], secondary_label=row.get("occurred_at")); add_edge(case_id, row["id"], "CASE_HAS_FORENSIC_EVENT", row["source_record_id"])
    related = related_cases(repository, user, purpose, case_id, source_system_ids, min(related_limit, 10))
    relation_edge_types = {"SHARED_ACCUSED": "CASE_SHARES_ACCUSED_WITH_CASE", "SHARED_COMPLAINANT": "CASE_SHARES_COMPLAINANT_WITH_CASE", "SHARED_VICTIM": "CASE_SHARES_VICTIM_WITH_CASE", "SHARED_ACT_SECTION": "CASE_SHARES_ACT_SECTION_WITH_CASE", "SHARED_POLICE_UNIT": "CASE_SHARES_UNIT_WITH_CASE", "SHARED_COURT": "CASE_SHARES_COURT_WITH_CASE", "SHARED_REGISTERING_OFFICER": "CASE_SHARES_OFFICER_WITH_CASE"}
    for candidate in related["related_cases"]:
        add_node(candidate["case_id"], "CASE", f"{candidate.get('crime_number') or candidate.get('fir_number')} · {candidate.get('case_number') or ''}".strip(), candidate["source_record_references"], secondary_label=candidate.get("legacy_status"), masked=candidate["masking"]["applied"])
        for reason in candidate["related_reasons"]:
            edge_type = relation_edge_types.get(reason["reason_type"])
            if edge_type: add_edge(case_id, candidate["case_id"], edge_type, reason["source_record_id"], projected=True, factual_basis=reason["label"])
    return {"graph": {"base_case_id": case_id, "nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges), "truncated": truncated, "selected_sources": list(dict.fromkeys(source_system_ids)), "limitations": "Bounded stored FIR relationships and projected D-7 reasons only.", "disclaimer": "Graph relationships are factual records or explained projections; they do not imply guilt, risk, identity, or recommendation."}, "textual_fallback": [f"{edge['source']} — {edge['relationship_type']} → {edge['target']}" for edge in edges]}


def fir_relationship_path(repository, user, purpose, case_id, target_node_id, source_system_ids, max_hops=3):
    """Return the shortest deterministic factual path within the bounded FIR graph."""
    try:
        hops = int(max_hops)
    except (TypeError, ValueError):
        raise ApiError("FIR_GRAPH_HOPS_INVALID", "Graph hops must be numeric.", 400, False)
    if not 1 <= hops <= 3:
        raise ApiError("FIR_GRAPH_HOPS_INVALID", "Graph hops must be between 1 and 3.", 400, False)
    result = fir_relationship_graph(repository, user, purpose, case_id, source_system_ids)
    graph_data = result["graph"]
    node_ids = {node["id"] for node in graph_data["nodes"]}
    if target_node_id not in node_ids:
        return {"path_nodes": [], "path_edges": [], "hop_count": 0, "max_hops": hops, "limitations": "Target is unavailable in the authorised bounded FIR graph.", "warning": "No factual path found."}
    adjacent = {}
    for edge in sorted(graph_data["edges"], key=lambda item: item["id"]):
        adjacent.setdefault(edge["source"], []).append((edge["target"], edge))
        adjacent.setdefault(edge["target"], []).append((edge["source"], edge))
    queue = deque([(case_id, [], [case_id])]); visited = {case_id}
    while queue:
        node_id, path_edges, path_nodes = queue.popleft()
        if node_id == target_node_id:
            return {"path_nodes": path_nodes, "path_edges": path_edges, "hop_count": len(path_edges), "max_hops": hops, "limitations": graph_data["limitations"]}
        if len(path_edges) >= hops:
            continue
        for next_id, edge in adjacent.get(node_id, []):
            if next_id not in visited:
                visited.add(next_id)
                queue.append((next_id, path_edges + [edge], path_nodes + [next_id]))
    return {"path_nodes": [], "path_edges": [], "hop_count": 0, "max_hops": hops, "limitations": graph_data["limitations"], "warning": "No factual path found."}
def discover(repository, user, purpose, plan):
    # Candidate discovery: only records a shared source-backed entity; never an identity claim.
    from backend.anvaya.services.search import search_cases
    bases = search_cases(repository, user, purpose, plan)
    output = []
    seen = set()
    request = DiscoveryRequest(tuple(dict.fromkeys(base["id"] for base in bases)), tuple(dict.fromkeys(plan.selected_sources)), min(plan.result_limit, 25)) if bases else None
    for candidate in repository.list_discovery_candidates(request) if request else []:
        if candidate["id"] in seen: continue
        decision = evaluate(user, purpose, plan.selected_sources, "DISCOVER", record_station=candidate["station_id"], record_district=candidate["district_id"])
        if not decision.allowed: continue
        seen.add(candidate["id"])
        label = "legacy compatibility relationship"
        result = mask_case({"id": candidate["id"], "fir_number": candidate["fir_number"], "offence": candidate["offence"], "incident_at": candidate["incident_at"], "status": candidate["status"], "station_id": candidate["station_id"], "district_id": candidate["district_id"], "relationship_reason": label, "relationship_type": candidate["relationship_type"], "candidate_relationship": True, "source_record_references": [candidate["source_record_id"], candidate["edge_source_record_id"], candidate["link_source_record_id"]], "freshness_state": candidate["freshness_state"], "jurisdiction_state": "assigned_station" if candidate["station_id"] == user["assigned_station"] else "external", "conflicts_limitations": "Candidate relationship only; not identity confirmation."}, decision.masking_level)
        output.append(result)
    return output[:min(plan.result_limit, 25)]


def relationship_path(repository, user, purpose, start_id, end_id, max_hops=3):
    request = RelationshipPathRequest(max_depth=max(1, min(int(max_hops), 3)))
    decision = evaluate(user, purpose, list(request.source_system_ids), "DISCOVER")
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)
    max_hops = request.max_depth
    rows = repository.list_relationship_edges(request)
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
