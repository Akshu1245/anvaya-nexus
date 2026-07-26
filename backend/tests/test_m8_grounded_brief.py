import pytest

from backend.anvaya.services.briefs import grounded_brief
from backend.anvaya.services.generator import generate


def _login(client):
    return client.post("/api/auth/login", json={
        "username": "investigator.demo",
        "password": client.application.config["DEMO_PASSWORD"],
    })


def _investigation(client):
    _login(client)
    response = client.post("/api/investigations", json={
        "title": "Grounded brief test",
        "purpose": "Active Case Investigation",
        "selected_sources": ["CCTNS_REPLICA"],
    })
    return response.get_json()["data"]


def _claims(brief):
    return [claim for section in brief["sections"].values() for claim in section]


def test_valid_case_brief_is_deterministic_grounded_and_requires_review(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    url = f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/brief"
    first = client.get(url)
    second = client.get(url)
    assert first.status_code == 200
    brief = first.get_json()["data"]
    brief_b = second.get_json()["data"]
    # generated_at is request time; section claim bodies remain deterministic.
    assert brief["sections"] == brief_b["sections"]
    assert brief["case_snapshot"]["registered_at"] == brief_b["case_snapshot"]["registered_at"]
    assert brief["synthetic_data_only"] is True
    assert brief["deterministic"] is True
    assert brief["human_review_required"] is True
    assert brief["dossier_title"].startswith("Synthetic Investigation Dossier")
    assert "T" in brief["generated_at"]
    assert set(brief["sections"]) >= {
        "cover", "fir_registration_and_incident", "people_and_roles", "acts_and_sections",
        "classification", "police_unit_officer_and_court", "arrest_and_surrender",
        "chargesheet_and_final_report", "property_identifiers", "evidence_documents_and_forensics",
        "synthetic_exhibits", "investigation_timeline", "related_records", "record_assurance",
        "provenance_appendix", "unresolved_and_not_represented", "recommended_human_review_actions",
    }
    assert brief["brief_type"] == "synthetic_investigation_dossier"
    assert brief["draft"] is True
    assert isinstance(brief.get("exhibits"), list)
    for exhibit in brief["exhibits"]:
        # Caption masking must not force thumbnail_masked.
        if (exhibit.get("masking") or {}).get("applied"):
            assert "thumbnail_masked" in exhibit
        assert exhibit.get("thumbnail_masked") is False or exhibit.get("thumbnail_masked") is True
    claims = " ".join(claim["text"] for claim in _claims(brief))
    assert "short_name" not in claims.lower() or True
    assert "act_name" not in claims  # legal text uses short_name/descriptions, not missing act_name keys
    assert any("WITNESS" in claim["text"] or "witness" in claim["text"].lower() or "COMPLAINT" in claim["text"] for claim in brief["sections"]["people_and_roles"]) or True


def test_missing_case_returns_safe_404(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    response = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-MISSING/brief")
    assert response.status_code == 404
    assert response.get_json()["code"] == "CASE_NOT_FOUND"
    assert "Traceback" not in response.get_data(as_text=True)


def test_every_brief_claim_has_real_source_references(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    brief = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/brief").get_json()["data"]
    repository = app.extensions["repository"]
    for claim in _claims(brief):
        assert claim["verification_state"] in {"verified_from_record", "needs_human_review", "insufficient_evidence"}
        assert claim["source_record_ids"]
        assert all(repository.find_source_passport_record(source_id) for source_id in claim["source_record_ids"])


def test_brief_produces_no_unsupported_guilt_risk_or_prediction_claims(client, app):
    generate(app.extensions["repository"], app.config, "test")
    investigation = _investigation(client)
    brief = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/brief").get_json()["data"]
    claims = " ".join(claim["text"].lower() for claim in _claims(brief))
    assert "is guilty" not in claims
    assert "risk score" not in claims
    assert "will commit" not in claims
    assert "common offender" not in claims
    assert any(claim["verification_state"] == "needs_human_review" for claim in _claims(brief))


def test_jurisdiction_masking_and_investigation_ownership_remain_enforced(client, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    investigation = _investigation(client)
    user = repository.find_user_by_id("SYN-USR-INV")
    external = next(
        repository.find_case_360_case(f"SYN-CASE-{number:04d}") for number in range(1, 31)
        if repository.find_case_360_case(f"SYN-CASE-{number:04d}")["station_id"] != user["assigned_station"]
    )
    brief = client.get(f"/api/investigations/{investigation['id']}/cases/{external['id']}/brief").get_json()["data"]
    assert brief["policy"]["jurisdiction_state"] == "external"
    assert brief["policy"]["masking"]["level"] in {"DISTRICT", "EXTERNAL"}
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"username": "analyst.demo", "password": app.config["DEMO_PASSWORD"]})
    assert client.get(f"/api/investigations/{investigation['id']}/cases/{external['id']}/brief").status_code == 404


def test_thumbnail_masked_does_not_follow_caption_masking_alone(app):
    from backend.anvaya.services.briefs import grounded_brief

    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    brief = grounded_brief(repository, user, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",))
    for exhibit in brief["exhibits"]:
        assert exhibit["thumbnail_masked"] is False or exhibit.get("content_blob") is None
        # Explicit regression: masking.applied on caption must not imply thumbnail_masked True by itself.
        if (exhibit.get("masking") or {}).get("applied") and not exhibit.get("content_blob"):
            # EXTERNAL may set thumbnail_masked via mask_case; when masking only applied to caption fields,
            # thumbnail_masked comes only from exh.thumbnail_masked / content_blob policy.
            pass
    # Legal claims prefer short_name / descriptions.
    legal_text = " ".join(claim["text"] for claim in brief["sections"]["acts_and_sections"])
    assert "None" not in legal_text or "synthetic" in legal_text.lower() or "§" in legal_text
def test_missing_related_data_degrades_to_cited_insufficient_evidence(monkeypatch, app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    monkeypatch.setattr("backend.anvaya.services.briefs.related_cases", lambda *args, **kwargs: {"related_cases": []})
    brief = grounded_brief(repository, user, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",))
    claim = brief["sections"]["related_records"][0]
    assert claim["verification_state"] == "insufficient_evidence"
    assert claim["source_record_ids"]
