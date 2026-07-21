from __future__ import annotations

from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.assurance import list_case_assurance
from backend.anvaya.services.investigation import case_360, related_cases


def compare_cases(repository, user, purpose, left_case_id, right_case_id, source_system_ids):
    """Side-by-side factual FIR comparison. No similarity score, identity, or guilt."""
    if left_case_id == right_case_id:
        raise ApiError("COMPARE_SAME_CASE", "Choose two different FIRs to compare.", 400, False)
    left = case_360(repository, user, purpose, left_case_id)
    right = case_360(repository, user, purpose, right_case_id)
    related = related_cases(repository, user, purpose, left_case_id, source_system_ids, limit=25)
    shared = next((item for item in related["related_cases"] if item["case_id"] == right_case_id), None)

    def snapshot(detail):
        fir = detail["case"]
        classification = detail.get("classification") or {}
        organisation = detail.get("police_and_court") or detail.get("organisation") or {}
        return {
            "case_id": fir["id"],
            "crime_number": fir.get("crime_number"),
            "case_number": fir.get("case_number"),
            "status": (fir.get("canonical_status") or {}).get("name") if isinstance(fir.get("canonical_status"), dict) else fir.get("legacy_status"),
            "registered_at": fir.get("registered_at"),
            "incident_from_at": (detail.get("incident") or {}).get("incident_from_at"),
            "incident_to_at": (detail.get("incident") or {}).get("incident_to_at"),
            "category": (classification.get("category") or {}).get("name"),
            "gravity": (classification.get("gravity") or {}).get("name"),
            "police_unit": organisation.get("unit_name"),
            "district": organisation.get("district_name"),
            "complainant_count": len((detail.get("people") or {}).get("complainants") or []),
            "victim_count": len((detail.get("people") or {}).get("victims") or []),
            "accused_count": len((detail.get("people") or {}).get("accused") or []),
            "legal_count": len((detail.get("legal_provisions") or {}).get("associations") or detail.get("legal") or []),
            "open_assurance": (detail.get("assurance") or {}).get("summary", {}).get("OPEN", 0),
            "source_record_id": fir.get("source_record_id"),
        }

    left_snap, right_snap = snapshot(left), snapshot(right)
    fields = [
        "status", "category", "gravity", "police_unit", "district",
        "complainant_count", "victim_count", "accused_count", "legal_count",
    ]
    shared_facts = []
    differing_facts = []
    for field in fields:
        left_value, right_value = left_snap.get(field), right_snap.get(field)
        if left_value is None and right_value is None:
            continue
        if left_value == right_value:
            shared_facts.append({"field": field, "value": left_value})
        else:
            differing_facts.append({"field": field, "left": left_value, "right": right_value})

    return {
        "left": left_snap,
        "right": right_snap,
        "shared_facts": shared_facts,
        "differing_facts": differing_facts,
        "related_reasons": (shared or {}).get("related_reasons", []),
        "limitations": [
            "Factual field comparison only.",
            "Shared values do not establish identity, common offender, guilt, or risk.",
            "Human review is required before any investigative conclusion.",
        ],
        "metadata": {
            "selected_sources": list(dict.fromkeys(source_system_ids)),
            "scoring": False,
            "human_review_required": True,
        },
    }


def verification_priorities(repository, user, purpose, case_id, source_system_ids):
    """Rank human-review actions from assurance, related facts, and source gaps."""
    detail = case_360(repository, user, purpose, case_id)
    assurance = list_case_assurance(repository, user, purpose, case_id, source_system_ids)
    related = related_cases(repository, user, purpose, case_id, source_system_ids, limit=5)
    cards = []

    for finding in assurance["findings"]:
        if finding["status"] != "OPEN":
            continue
        if finding["severity"] not in {"BLOCKING", "WARNING"}:
            continue
        cards.append(
            {
                "id": finding["id"],
                "title": finding["title"],
                "priority_band": "HIGH" if finding["severity"] == "BLOCKING" else "MEDIUM",
                "why": [finding["factual_explanation"], f"Severity {finding['severity']}"],
                "source_record_ids": finding["source_record_ids"],
                "category": "record_assurance",
                "action": "review_only",
                "limitations": [
                    "Suggested verification priority — not a legal direction, guilt finding, or arrest recommendation."
                ],
            }
        )

    for source in detail.get("sources") or detail.get("source_records") or []:
        if source.get("freshness_state") in {"Stale", "Unavailable"} or source.get("warning"):
            cards.append(
                {
                    "id": f"source-{source.get('source_record_id')}",
                    "title": f"Review source state: {source.get('source_system') or 'Source'}",
                    "priority_band": "MEDIUM",
                    "why": [
                        source.get("warning") or f"Freshness state is {source.get('freshness_state')}",
                        f"Reliability role: {source.get('reliability_role')}",
                    ],
                    "source_record_ids": [source.get("source_record_id")],
                    "category": "source_gap",
                    "action": "review_only",
                    "limitations": ["Source-state prompt only; no automatic correction is applied."],
                }
            )

    for candidate in related["related_cases"][:5]:
        reasons = candidate.get("related_reasons") or []
        if not reasons:
            continue
        cards.append(
            {
                "id": f"related-{candidate['case_id']}",
                "title": f"Review factual relationship to {candidate.get('crime_number') or candidate['case_id']}",
                "priority_band": "MEDIUM" if candidate.get("direct_reason_count") else "LOW",
                "why": [
                    f"{reason['label']}"
                    + (f": {reason['factual_value']}" if reason.get("factual_value") else "")
                    for reason in reasons[:3]
                ],
                "source_record_ids": [
                    reason.get("source_record_id") for reason in reasons if reason.get("source_record_id")
                ]
                + candidate.get("source_record_references", []),
                "category": "related_fact",
                "action": "review_only",
                "limitations": [related["metadata"]["limitations"]],
            }
        )

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    cards.sort(key=lambda item: (order.get(item["priority_band"], 9), item["title"], item["id"]))
    return {
        "case_id": case_id,
        "priorities": cards[:15],
        "summary": {
            "high": sum(item["priority_band"] == "HIGH" for item in cards),
            "medium": sum(item["priority_band"] == "MEDIUM" for item in cards),
            "low": sum(item["priority_band"] == "LOW" for item in cards),
        },
        "limitations": [
            "Suggested verification priority only.",
            "Not a legal direction, guilt finding, identity match, person-risk score, or arrest recommendation.",
            "Human review required.",
        ],
    }
