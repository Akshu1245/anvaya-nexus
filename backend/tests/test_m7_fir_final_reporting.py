from backend.anvaya.services.generator import generate


def _login(client):
    return client.post(
        "/api/auth/login",
        json={"username": "investigator.demo", "password": client.application.config["DEMO_PASSWORD"]},
    )


def _investigation(client):
    return client.post(
        "/api/investigations",
        json={
            "title": "FIR final reporting fixture",
            "purpose": "Active Case Investigation",
            "selected_sources": ["CCTNS_REPLICA"],
        },
    ).json["data"]


def test_primary_fir_report_catalogue_is_safe_and_deterministic(client, app):
    generate(app.extensions["repository"], app.config, "test")
    assert _login(client).status_code == 200
    investigation = _investigation(client)
    sections = [
        "Cover",
        "FIR Header and Incident Summary",
        "Related Cases and Matching Reasons",
        "FIR Relationship Graph",
        "FIR Record Assurance",
        "Sources and Provenance",
        "Disclaimer",
    ]
    response = client.post(
        "/api/reports",
        json={
            "title": "Synthetic FIR report",
            "investigation_id": investigation["id"],
            "sections": sections + ["Cover"],
            "notes": "Bounded factual summary.",
        },
    )
    assert response.status_code == 201
    html = response.json["data"]["html"]
    assert html.index("FIR Header and Incident Summary") < html.index("FIR Record Assurance")
    assert "Structured factual relationship summary only" in html
    assert "never alter FIR records automatically" in html
    assert "payload_json" not in html
    assert "synthetic-auth-fixture" not in html


def test_empty_or_markup_report_input_is_rejected(client, app):
    generate(app.extensions["repository"], app.config, "test")
    assert _login(client).status_code == 200
    investigation = _investigation(client)
    base = {"investigation_id": investigation["id"], "title": "Synthetic FIR report"}
    empty = client.post("/api/reports", json={**base, "sections": []})
    unsafe = client.post("/api/reports", json={**base, "sections": ["Cover"], "notes": "<markup>"})
    assert empty.status_code == 400 and empty.json["code"] == "REPORT_SECTIONS_REQUIRED"
    assert unsafe.status_code == 400 and unsafe.json["code"] == "REPORT_INPUT_INVALID"
