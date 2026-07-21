from __future__ import annotations

from datetime import datetime, timezone

from backend.anvaya.services.investigation import case_360, related_cases


def _claim(text, state, *source_ids):
    return {
        "text": text,
        "verification_state": state,
        "source_record_ids": list(dict.fromkeys(source_id for source_id in source_ids if source_id)),
    }


def _not_represented(*source_ids):
    return _claim(
        "Not represented in authorised synthetic records.",
        "insufficient_evidence",
        *source_ids,
    )


def _name(value):
    if isinstance(value, dict):
        return value.get("name") or value.get("code") or value.get("display_name") or "not recorded"
    return value or "not recorded"


def grounded_brief(repository, user, purpose, case_id, source_system_ids):
    """Build a sectioned synthetic investigation dossier from authorised, masked records."""
    detail = case_360(repository, user, purpose, case_id)
    case = detail["case"]
    incident = detail["incident"]
    overview = detail["overview"]
    base_source = case["source_record_id"]
    status = _name(case.get("canonical_status") or case.get("legacy_status"))
    org = detail.get("police_and_court") or detail.get("organisation") or {}

    cover = [
        _claim(
            "Synthetic Investigation Dossier (DRAFT) — IIF-inspired worksheet fields only; not an official FIR form.",
            "verified_from_record",
            base_source,
        ),
        _claim(
            f"DRAFT synthetic investigation dossier for {case.get('crime_number') or case.get('fir_number') or case_id}.",
            "verified_from_record",
            base_source,
        ),
        _claim(
            f"Station / unit: {_name(org.get('unit_name'))}; district: {_name(org.get('district_name'))}; "
            f"registering officer: {_name(org.get('officer_name'))}; case IO: {_name((org.get('investigating_officer') or {}).get('display_name') or org.get('investigating_officer_name'))}; "
            f"registration datetime: {case.get('registered_at') or 'not recorded'}.",
            "verified_from_record",
            base_source,
        ),
        _claim(
            f"Jurisdiction state: {overview.get('jurisdiction_state') or 'not recorded'}; masking level: {(overview.get('masking') or {}).get('level') or 'NONE'}.",
            "verified_from_record",
            base_source,
        ),
        _claim(
            f"Selected sources for this dossier: {', '.join(source_system_ids) or 'none'}.",
            "verified_from_record",
            base_source,
        ),
    ]

    fir_registration = [
        _claim(
            f"FIR {case.get('fir_number') or 'not recorded'} · crime {case.get('crime_number') or 'not recorded'} · case {case.get('case_number') or 'not recorded'} registered at {case.get('registered_at') or 'an unrecorded time'} with status {status}.",
            "verified_from_record",
            base_source,
        ),
        _claim(
            f"Offence category recorded on the case record: {overview.get('offence') or 'not recorded'}.",
            "verified_from_record",
            base_source,
        ),
    ]
    if incident.get("brief_facts"):
        fir_registration.append(_claim(incident["brief_facts"], "verified_from_record" if not incident.get("brief_facts_masked") else "needs_human_review", incident["source_record_id"]))
    fir_registration.append(_claim(
        f"Incident window: {incident.get('incident_from_at') or 'not recorded'} to {incident.get('incident_to_at') or 'not recorded'}; information received: {incident.get('information_received_at') or 'not recorded'}.",
        "verified_from_record",
        incident["source_record_id"],
    ))

    people_claims = []
    for group in ("complainants", "victims", "accused", "witnesses"):
        for person in detail["people"].get(group) or []:
            people_claims.append(_claim(
                f"{person['display_name']} is recorded with the role {person['role']}"
                + (f" (sequence {person['role_sequence']})" if person.get("role_sequence") else "") + ".",
                "verified_from_record",
                person["source_record_id"],
            ))
    if not people_claims:
        people_claims = [_not_represented(base_source)]
    for statement in detail.get("statements") or []:
        people_claims.append(_claim(
            f"{statement.get('statement_type') or 'STATEMENT'} by {statement.get('display_name') or 'recorded person'} "
            f"at {statement.get('recorded_at') or 'unrecorded time'} ({statement.get('language_code') or 'lang n/a'}): "
            f"{statement.get('body_text') or 'body not represented'}.",
            "verified_from_record" if not (statement.get("masking") or {}).get("applied") else "needs_human_review",
            statement.get("source_record_id") or base_source,
        ))

    legal_claims = []
    for link in detail.get("legal") or []:
        act_label = link.get("short_name") or link.get("act_description") or link.get("act_code") or link.get("act_id")
        section_label = link.get("section_description") or link.get("section_code") or link.get("section_id")
        legal_claims.append(_claim(
            f"Act {link.get('act_code') or link.get('act_id')} ({act_label}) § {link.get('section_code') or link.get('section_id')} "
            f"({section_label}) is associated with this case.",
            "verified_from_record",
            link.get("source_record_id") or base_source,
        ))
    if not legal_claims:
        legal_claims = [_not_represented(base_source)]

    classification = detail.get("classifications") or detail.get("classification") or {}
    classification_claims = [
        _claim(f"Case category: {_name(classification.get('category'))}.", "verified_from_record" if classification.get("category") else "insufficient_evidence", base_source),
        _claim(f"Gravity: {_name(classification.get('gravity'))}.", "verified_from_record" if classification.get("gravity") else "insufficient_evidence", base_source),
        _claim(f"Major crime head: {_name(classification.get('crime_major_head'))}; minor sub-head: {_name(classification.get('crime_minor_head'))}.", "verified_from_record" if classification.get("crime_major_head") else "insufficient_evidence", base_source),
        _claim(f"Canonical status: {_name(classification.get('canonical_status'))}.", "verified_from_record" if classification.get("canonical_status") else "insufficient_evidence", base_source),
    ]

    organisation_claims = [
        _claim(
            f"Registering unit: {_name(org.get('unit_name') or (org.get('police_unit') or {}).get('name'))}; "
            f"district: {_name(org.get('district_name') or (org.get('district') or {}).get('name'))}; "
            f"state: {_name(org.get('state_name') or (org.get('state') or {}).get('name'))}.",
            "verified_from_record" if org else "insufficient_evidence",
            base_source,
        ),
        _claim(
            f"Registering officer: {_name(org.get('officer_name'))} "
            f"(rank {_name(org.get('rank_name'))}, designation {_name(org.get('designation_name'))}).",
            "verified_from_record" if org.get("officer_name") else "insufficient_evidence",
            base_source,
        ),
        _claim(
            f"Investigating officer (case IO): {_name((org.get('investigating_officer') or {}).get('display_name') or org.get('investigating_officer_name'))} "
            f"(rank {_name((org.get('investigating_officer') or {}).get('rank_name') or org.get('investigating_rank_name'))}).",
            "verified_from_record" if (org.get("investigating_officer") or org.get("investigating_officer_name")) else "insufficient_evidence",
            base_source,
        ),
        _claim(
            f"Court of record: {_name(org.get('court_name') or (org.get('court') or {}).get('name'))}.",
            "verified_from_record" if (org.get("court_name") or org.get("court")) else "insufficient_evidence",
            base_source,
        ),
    ]

    arrest_claims = []
    for event in detail.get("arrests") or []:
        io = ((event.get("organisation") or {}).get("investigating_officer") or {})
        arrest_claims.append(_claim(
            f"{event.get('event_type')} recorded at {event.get('event_at')}; investigating officer {_name(io.get('display_name'))}; "
            f"remarks: {event.get('remarks') or 'not recorded'}. Linked accused count: {len(event.get('accused') or [])}.",
            "verified_from_record",
            event.get("source_record_id"),
        ))
    if not arrest_claims:
        arrest_claims = [_not_represented(base_source)]

    chargesheet_claims = []
    for row in detail.get("chargesheets") or []:
        officer = row.get("filing_officer") or {}
        chargesheet_claims.append(_claim(
            f"{row.get('report_type')} filed at {row.get('filed_at')} by {_name(officer.get('display_name'))}. "
            f"Summary: {row.get('summary') or 'not recorded'}.",
            "verified_from_record",
            row.get("source_record_id"),
        ))
    if not chargesheet_claims:
        chargesheet_claims = [_not_represented(base_source)]

    property_claims = []
    for item in detail.get("property_identifiers") or []:
        property_claims.append(_claim(
            f"{item['type']} identifier recorded as {item.get('value') or 'masked/unavailable'} (target {item.get('target_id')}).",
            "verified_from_record",
            item.get("source_record_id") or base_source,
        ))
    if not property_claims:
        property_claims = [_not_represented(base_source)]

    evidence_claims = []
    for row in detail.get("evidence") or []:
        evidence_claims.append(_claim(
            f"Evidence {row.get('id')}: type {row.get('evidence_type')}; status {row.get('status')}; "
            f"description {row.get('description') or 'not recorded'}; sensitivity {row.get('sensitivity') or 'not recorded'}.",
            "verified_from_record",
            row.get("source_record_id"),
        ))
    for doc in detail.get("documents") or []:
        evidence_claims.append(_claim(
            f"Document {doc.get('id')}: type {doc.get('document_type')}; status {doc.get('status')}.",
            "verified_from_record",
            doc.get("source_record_id"),
        ))
    forensics = (detail.get("evidence_section") or {}).get("forensic_events") or []
    for event in forensics:
        evidence_claims.append(_claim(
            f"Forensic event {event.get('id')}: {event.get('event_type')} at {event.get('occurred_at')}; result {event.get('result_status') or 'not recorded'}.",
            "verified_from_record",
            event.get("source_record_id"),
        ))
    if not evidence_claims:
        evidence_claims = [_not_represented(base_source)]

    exhibit_claims = []
    exhibit_records = []
    for exh in detail.get("exhibits") or []:
        custody_bits = []
        for event in exh.get("custody_events") or []:
            custody_bits.append(f"{event.get('event_type')}@{event.get('event_at')}")
        custody_text = ("; ".join(custody_bits)) if custody_bits else "no custody events recorded"
        exhibit_claims.append(_claim(
            f"Synthetic exhibit {exh.get('exhibit_code')} ({exh.get('exhibit_kind') or 'untyped'}): {exh.get('caption')}; MIME {exh.get('mime_type')}; "
            f"SHA-256 {exh.get('sha256')}; chain {exh.get('chain_status')}; collected {exh.get('collected_at')}; custody {custody_text}. "
            "Watermarked placeholder only — not operational evidence.",
            "verified_from_record",
            exh.get("source_record_id"),
            *[event.get("source_record_id") for event in (exh.get("custody_events") or []) if event.get("source_record_id")],
        ))
        exhibit_records.append({
            "id": exh.get("id"),
            "exhibit_code": exh.get("exhibit_code"),
            "exhibit_kind": exh.get("exhibit_kind"),
            "filename": exh.get("filename"),
            "mime_type": exh.get("mime_type"),
            "sha256": exh.get("sha256"),
            "caption": exh.get("caption"),
            "chain_status": exh.get("chain_status"),
            "collected_at": exh.get("collected_at"),
            "source_record_id": exh.get("source_record_id"),
            "custody_events": exh.get("custody_events") or [],
            # Thumbnail masking is EXTERNAL/policy thumbnail flag only — never conflate caption masking.
            "thumbnail_masked": bool(exh.get("thumbnail_masked")),
            "masking": exh.get("masking"),
        })
    if not exhibit_claims:
        exhibit_claims = [_not_represented(base_source)]

    timeline = [
        _claim(f"{event['label']} at {event['at']}.", "verified_from_record", event["source_record_id"])
        for event in detail["timeline"]
    ] or [_not_represented(base_source)]

    related = related_cases(repository, user, purpose, case_id, source_system_ids, 5)
    related_claims = []
    for record in related["related_cases"]:
        reason_labels = ", ".join(reason["label"] for reason in record["related_reasons"])
        references = record["source_record_references"] + [reason["source_record_id"] for reason in record["related_reasons"]]
        related_claims.append(_claim(
            f"{record['case_id']} is a candidate related record because stored records show: {reason_labels}. "
            "This connection does not imply guilt or identity.",
            "needs_human_review",
            *references,
        ))
    if not related_claims:
        related_claims.append(_claim(
            "No related records are available from the selected authorised sources.",
            "insufficient_evidence",
            base_source,
        ))

    warnings = [
        _claim(
            f"{finding['title']}: {finding['factual_explanation']}",
            "needs_human_review",
            *finding["source_record_ids"],
        )
        for finding in detail["data_quality"]
        if finding.get("source_record_ids")
    ]
    if not warnings:
        warnings.append(_claim(
            "No deterministic data-quality warnings are recorded; completeness still requires human review.",
            "needs_human_review",
            base_source,
        ))

    provenance = []
    provenance_ids = []
    for section_claims in (
        cover, fir_registration, people_claims, legal_claims, classification_claims, organisation_claims,
        arrest_claims, chargesheet_claims, property_claims, evidence_claims, exhibit_claims, timeline,
        related_claims, warnings,
    ):
        for claim in section_claims:
            provenance_ids.extend(claim.get("source_record_ids") or [])
    for source_id in dict.fromkeys(provenance_ids):
        source = next((item for item in (detail.get("sources") or detail.get("source_records") or []) if item.get("source_record_id") == source_id), None)
        if source is None:
            source = {"source_record_id": source_id, "available": True, "source_system": "Authorised synthetic source", "freshness_state": "Unknown", "reliability_role": "fixture", "source_limitations": "Union of section claim references."}
        if not source.get("available", True):
            provenance.append(_claim(f"Source {source.get('source_record_id')}: provenance unavailable.", "insufficient_evidence", source.get("source_record_id") or base_source))
            continue
        provenance.append(_claim(
            f"{source.get('source_record_id')} · system {source.get('source_system')} · freshness {source.get('freshness_state')} · "
            f"reliability {source.get('reliability_role')} · limitation: {source.get('source_limitations') or 'none recorded'}.",
            "verified_from_record",
            source.get("source_record_id"),
        ))
    if not provenance:
        provenance = [_not_represented(base_source)]

    unresolved = [
        _claim("Case diary entries are not represented in authorised synthetic records.", "insufficient_evidence", base_source),
        _claim("Mahazar / panchnama narrative detail is not represented in authorised synthetic records.", "insufficient_evidence", base_source),
        _claim("Remand / bail chronology and court-hearing annexures are not represented in authorised synthetic records.", "insufficient_evidence", base_source),
        _claim(
            "Confirm whether each open data-quality warning reflects a source-record error or a valid event sequence.",
            "needs_human_review",
            *(source_id for warning in warnings for source_id in warning["source_record_ids"]),
        ),
    ]
    actions = [
        _claim(
            "Review cited source passports and resolve or acknowledge open Record Assurance findings before relying on this dossier.",
            "needs_human_review",
            *(source_id for warning in warnings for source_id in warning["source_record_ids"]),
        ),
        _claim(
            "Manually compare related-case records; do not infer identity, guilt, or risk from a relationship alone.",
            "needs_human_review",
            *(source_id for claim in related_claims for source_id in claim["source_record_ids"]),
        ),
        _claim(
            "Treat synthetic exhibit images as watermarked placeholders only; they are not operational scene or seizure photographs.",
            "needs_human_review",
            *(source_id for claim in exhibit_claims for source_id in claim["source_record_ids"]),
        ),
    ]

    sections = {
        "cover": cover,
        "fir_registration_and_incident": fir_registration,
        "people_and_roles": people_claims,
        "acts_and_sections": legal_claims,
        "classification": classification_claims,
        "police_unit_officer_and_court": organisation_claims,
        "arrest_and_surrender": arrest_claims,
        "chargesheet_and_final_report": chargesheet_claims,
        "property_identifiers": property_claims,
        "evidence_documents_and_forensics": evidence_claims,
        "synthetic_exhibits": exhibit_claims,
        "investigation_timeline": timeline,
        "related_records": related_claims,
        "record_assurance": warnings,
        "provenance_appendix": provenance,
        "unresolved_and_not_represented": unresolved,
        "recommended_human_review_actions": actions,
    }

    return {
        "brief_type": "synthetic_investigation_dossier",
        "dossier_title": "Synthetic Investigation Dossier (DRAFT)",
        "case_id": case_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_data_only": True,
        "deterministic": True,
        "human_review_required": True,
        "draft": True,
        "case_snapshot": {
            "fir_number": case.get("fir_number"),
            "crime_number": case.get("crime_number"),
            "case_number": case.get("case_number"),
            "status": status,
            "registered_at": case.get("registered_at"),
            "offence": overview.get("offence"),
            "station": org.get("unit_name"),
            "district": org.get("district_name"),
            "registering_officer": org.get("officer_name"),
            "investigating_officer": (org.get("investigating_officer") or {}).get("display_name") or org.get("investigating_officer_name"),
        },
        "policy": {
            "jurisdiction_state": overview.get("jurisdiction_state"),
            "masking": overview.get("masking", {"applied": False, "level": "NONE", "fields": []}),
            "selected_sources": list(dict.fromkeys(source_system_ids)),
        },
        "exhibits": exhibit_records,
        "sections": sections,
        "limitations": [
            "Synthetic data only; DRAFT · HUMAN REVIEW REQUIRED · NOT FOR OPERATIONAL USE.",
            "This is not a BNSS s.193 / CrPC s.173 charge-sheet and not a live CCTNS export.",
            "Record roles and relationships do not imply identity, guilt, culpability, or risk.",
            "Synthetic exhibit images are watermarked placeholders and must never be treated as operational evidence.",
            "Decorative offence-category icons are not exhibits and are not included in this dossier.",
            "Case diary, mahazar detail, remand/bail chronology and court-hearing annexures are not represented.",
        ],
    }
