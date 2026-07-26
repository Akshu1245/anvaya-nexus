"""Deterministic evaluation harness for measured Shift Intelligence claims only."""
from __future__ import annotations

import time
from datetime import date

from backend.anvaya.services.assurance import list_case_assurance
from backend.anvaya.services.briefing import build_shift_briefing
from backend.anvaya.services.generator import generate, ground_truth_manifest
from backend.anvaya.services.investigation import related_cases
from backend.anvaya.services.query_parser import parse_query
from backend.anvaya.services.search import search_cases


def test_evaluation_harness_measures_seeded_quality_and_related_coverage(client, app):
    repo = app.extensions["repository"]
    generate(repo, app.config, "test")
    truth = ground_truth_manifest()
    user = repo.find_user_by_id("SYN-USR-INV")
    client.post(
        "/api/auth/login",
        json={"username": "investigator.demo", "password": app.config["DEMO_PASSWORD"]},
    )
    investigation = client.post(
        "/api/investigations",
        json={
            "title": "Evaluation harness",
            "purpose": "Active Case Investigation",
            "selected_sources": ["CCTNS_REPLICA"],
        },
    ).get_json()["data"]

    started = time.perf_counter()
    briefing_one = build_shift_briefing(repo, user, "Active Case Investigation", ["CCTNS_REPLICA"])
    briefing_two = build_shift_briefing(repo, user, "Active Case Investigation", ["CCTNS_REPLICA"])
    briefing_ms = (time.perf_counter() - started) * 1000
    assert briefing_one == briefing_two
    assert briefing_ms < 20000

    defect_cases = ["SYN-CASE-0001", "SYN-CASE-0005", "SYN-CASE-0007"]
    detected = 0
    for case_id in defect_cases:
        findings = list_case_assurance(
            repo, user, "Active Case Investigation", case_id, ["CCTNS_REPLICA"]
        )["findings"]
        if any(item["status"] == "OPEN" for item in findings):
            detected += 1
    assert detected / len(defect_cases) >= 0.66

    plan = parse_query(
        "Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.",
        ["CCTNS_REPLICA"],
        today=date(2026, 7, 11),
    )
    assert plan.intent == "SEARCH"
    results = search_cases(repo, user, "Active Case Investigation", plan)
    assert len(results) >= 1

    related = related_cases(repo, user, "Active Case Investigation", "SYN-CASE-0001", ["CCTNS_REPLICA"], limit=5)
    top_ids = [item["case_id"] for item in related["related_cases"][:5]]
    assert "SYN-CASE-0002" in top_ids

    response = client.get(f"/api/investigations/{investigation['id']}/analytics/briefing")
    assert response.status_code == 200
    assert response.get_json()["data"]["summary"]["authorised_case_count"] > 0
    assert truth.get("synthetic_only") is True
    assert "seeded_defects" in truth
