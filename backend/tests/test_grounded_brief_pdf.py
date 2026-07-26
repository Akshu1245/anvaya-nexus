from backend.anvaya.services.brief_pdf import grounded_brief_pdf
from backend.anvaya.services.exhibit_assets import render_synthetic_exhibit_png, sha256_bytes
from backend.anvaya.services.generator import generate


def test_grounded_brief_pdf_is_a_real_pdf_document():
    payload = {
        "case_id": "SYN-CASE-0001",
        "dossier_title": "Synthetic Investigation Dossier",
        "case_snapshot": {
            "fir_number": "SYN-FIR-000001",
            "crime_number": "SYN-CRIME-00001",
            "status": "UNRESOLVED",
            "investigating_officer": "ಅನ್ವಯ / अन्वेषक",
            "station": "Synthetic Station",
        },
        "policy": {"jurisdiction_state": "assigned_station", "masking": {"level": "NONE"}, "selected_sources": ["CCTNS_REPLICA"]},
        "sections": {
            "cover": [{"text": "Synthetic case record.", "source_record_ids": ["SRC-1"], "verification_state": "verified_from_record"}],
            "synthetic_exhibits": [{"text": "Exhibit EXH-0001-01", "source_record_ids": ["SRC-1"], "verification_state": "verified_from_record"}],
        },
        "exhibits": [],
        "limitations": ["Synthetic data only."],
    }
    document = grounded_brief_pdf(payload, "Synthetic investigation")
    assert document.startswith(b"%PDF")
    assert b"ANVAYA" in document
    assert b"DOSSIER" in document.upper() or b"Dossier" in document or b"Investigation" in document
    assert b"offence-icons" not in document


def test_dossier_pdf_embeds_synthetic_exhibit_and_excludes_offence_icons(client, app):
    generate(app.extensions["repository"], app.config, "test")
    client.post("/api/auth/login", json={"username": "investigator.demo", "password": app.config["DEMO_PASSWORD"]})
    inv = client.post("/api/investigations", json={
        "title": "Dossier PDF test",
        "purpose": "Active Case Investigation",
        "selected_sources": ["CCTNS_REPLICA"],
    }).json["data"]
    brief = client.get(f"/api/investigations/{inv['id']}/cases/SYN-CASE-0001/brief").json["data"]
    assert brief["exhibits"], "seeded case should include synthetic exhibits"
    response = client.get(f"/api/investigations/{inv['id']}/cases/SYN-CASE-0001/brief.pdf")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/pdf")
    body = response.data
    assert body.startswith(b"%PDF")
    assert b"offence-icons" not in body
    # Title/subject/keywords live in the PDF Info dict (uncompressed).
    assert b"ANVAYA Synthetic Investigation Dossier" in body
    assert b"SYNTHETIC" in body
    assert brief["exhibits"][0]["exhibit_code"].encode() in body


def test_synthetic_exhibit_png_is_watermarked_and_hashed():
    blob = render_synthetic_exhibit_png(exhibit_code="EXH-TEST-01", caption="Synthetic caption", case_id="SYN-CASE-0001")
    assert blob.startswith(b"\x89PNG")
    assert len(sha256_bytes(blob)) == 64
