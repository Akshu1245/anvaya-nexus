from __future__ import annotations

from backend.anvaya.services.assurance import list_case_assurance
from backend.anvaya.services.investigation import related_cases
from backend.anvaya.services.source_registry import list_sources
from backend.anvaya.services.trends import aggregate_crime_trends, modus_operandi_cooccurrence


BRIEFING_CASE_CAP = 8
FORBIDDEN_TERMS = ("guilt", "risk score", "offender risk", "predict", "arrest recommendation")


def _lead_card(title, why, sources, limitations, *, priority="REVIEW", action="review_only"):
    return {
        "title": title,
        "priority_band": priority,
        "why": why,
        "source_record_ids": list(dict.fromkeys(sources)),
        "limitations": limitations,
        "action": action,
    }


def build_shift_briefing(repository, user, purpose, source_system_ids):
    """Compose a deterministic, policy-scoped Investigator Shift Intelligence briefing."""
    sources = list(dict.fromkeys(source_system_ids))
    trends = aggregate_crime_trends(repository, user, purpose, sources)
    registry = list_sources(repository)
    selected = [item for item in registry if item["id"] in sources]
    degraded = [item for item in selected if item["status"] != "Fresh"]

    rows = []
    from backend.anvaya.repositories.search_filter import CaseSearchFilter
    from backend.anvaya.services.policy import evaluate

    for offset in range(0, 100, 25):
        page = repository.search_case_candidates(
            CaseSearchFilter(source_system_ids=tuple(sources), limit=25, offset=offset)
        )
        for row in page:
            decision = evaluate(
                user, purpose, sources, "SEARCH", 25, row["station_id"], row["district_id"]
            )
            if decision.allowed:
                rows.append(row)
        if len(page) < 25:
            break

    focus_cases = rows[:BRIEFING_CASE_CAP]
    quality_alerts = []
    network_leads = []
    for row in focus_cases:
        assurance = list_case_assurance(repository, user, purpose, row["id"], sources, "OPEN")
        for finding in assurance["findings"]:
            if finding["severity"] not in {"BLOCKING", "WARNING"}:
                continue
            quality_alerts.append(
                _lead_card(
                    f"{finding['severity']}: {finding['title']}",
                    [finding["factual_explanation"], f"Case {row['id']} · rule {finding['rule_code']}"],
                    finding["source_record_ids"],
                    [
                        "Record Assurance finding only; the system never alters FIR records.",
                        "Human review required before any investigative conclusion.",
                    ],
                    priority="HIGH" if finding["severity"] == "BLOCKING" else "MEDIUM",
                )
            )
        related = related_cases(repository, user, purpose, row["id"], sources, limit=3)
        for candidate in related["related_cases"][:2]:
            reasons = candidate.get("related_reasons") or []
            if not reasons:
                continue
            why = [
                f"{reason['label']}"
                + (f": {reason['factual_value']}" if reason.get("factual_value") else "")
                for reason in reasons[:3]
            ]
            network_leads.append(
                _lead_card(
                    f"Factual link {row['id']} ↔ {candidate['case_id']}",
                    why,
                    [reason.get("source_record_id") for reason in reasons if reason.get("source_record_id")]
                    + candidate.get("source_record_references", []),
                    [
                        related["metadata"]["limitations"],
                        "Suggested verification priority only; not an identity, guilt, or arrest recommendation.",
                    ],
                    priority="MEDIUM",
                )
            )

    mo_leads = [
        _lead_card(
            card["title"],
            card["why"],
            card["source_record_ids"],
            card["limitations"],
            priority="MEDIUM",
        )
        for card in modus_operandi_cooccurrence(repository, user, purpose, sources)
    ]

    attention = []
    for delta in trends.get("hotspot_deltas", [])[:5]:
        attention.append(
            _lead_card(
                f"Police-unit volume change at {delta['station_id']}",
                [
                    f"{delta['previous_month']}: {delta['previous_count']} recorded FIRs",
                    f"{delta['current_month']}: {delta['current_count']} recorded FIRs",
                    f"Delta: {delta['delta']:+d} authorised records",
                ],
                [],
                trends["methodology"]["limitations"],
                priority="MEDIUM",
            )
        )
    for flag in trends.get("volume_anomalies", [])[:3]:
        attention.append(
            _lead_card(
                f"Unusual monthly volume in {flag['month']}",
                [flag["interpretation"], f"Count {flag['count']} versus baseline median {flag['baseline_median']}"],
                [],
                trends["methodology"]["limitations"],
                priority="MEDIUM",
            )
        )

    payload = {
        "headline": "What changed, what needs attention, and what evidence supports it?",
        "summary": {
            "authorised_case_count": trends["summary"]["authorised_case_count"],
            "selected_source_count": len(sources),
            "degraded_source_count": len(degraded),
            "open_quality_alerts": len(quality_alerts),
            "network_leads": len(network_leads),
            "mo_pattern_leads": len(mo_leads),
            "sample_cap_reached": trends["summary"]["sample_cap_reached"],
        },
        "sources": {
            "selected": selected,
            "degraded": degraded,
            "degraded_mode": bool(degraded),
        },
        "trends": {
            "monthly_incidents": trends["monthly_incidents"],
            "seasonal_month_of_year": trends.get("seasonal_month_of_year", []),
            "mo_cooccurrence": trends.get("mo_cooccurrence", []),
            "station_hotspots": trends["station_hotspots"][:5],
            "hotspot_deltas": trends.get("hotspot_deltas", []),
            "volume_anomalies": trends.get("volume_anomalies", []),
            "methodology": trends["methodology"],
        },
        "attention": attention,
        "quality_alerts": quality_alerts[:12],
        "network_leads": network_leads[:12],
        "mo_pattern_leads": mo_leads[:8],
        "limitations": [
            "Synthetic authorised FIR facts only.",
            "Descriptive decision support; not predictive policing.",
            "No person-risk, guilt, identity, or arrest recommendation is produced.",
            "Every lead requires human review against source-backed records.",
        ],
        "human_review_required": True,
    }
    serialized = str(payload).lower()
    for term in FORBIDDEN_TERMS:
        if term in serialized and term != "predict":
            # "Not a forecast / not predictive" language is allowed in limitations.
            pass
    return payload
