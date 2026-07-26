from backend.anvaya.services.official_fir import seed_official_fir_fixture

PASSWORD = "ANVAYA-DEMO-ONLY-2026"
CASE = "FIR-CASE-0001"


def login(client):
    response = client.post("/api/auth/login", json={"username": "investigator.demo", "password": PASSWORD})
    assert response.status_code == 200


def prepare(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)


def test_grounded_brief_is_cited_and_synthetic(client, app):
    prepare(client, app)
    response = client.get(f"/api/fir/cases/{CASE}/brief")
    assert response.status_code == 200
    data = response.json["data"]
    assert data["generated_by"] == "deterministic_grounded_template"
    assert data["statements"] and all(item["source_references"] for item in data["statements"])
    assert "Synthetic" in " ".join(data["limitations"])


def test_related_identity_and_human_review_have_no_auto_merge(client, app):
    prepare(client, app)
    related = client.get(f"/api/fir/cases/{CASE}/related-cases").json["data"]["results"]
    assert related and related[0]["human_review_required"] is True
    suggestions = client.get(f"/api/fir/cases/{CASE}/identity-suggestions").json["data"]["suggestions"]
    assert suggestions and suggestions[0]["automatic_merge"] is False
    suggestion = suggestions[0]
    response = client.post(f"/api/fir/cases/{CASE}/identity-suggestions/review", json={
        "related_case_id": suggestion["right_case_id"], "person_id": suggestion["shared_person_id"],
        "decision": "NEEDS_REVIEW", "note": "Synthetic test review",
    })
    assert response.status_code == 200
    assert response.json["data"]["automatic_merge"] is False


def test_assurance_and_factual_graph(client, app):
    prepare(client, app)
    assurance = client.get(f"/api/fir/cases/{CASE}/assurance")
    assert assurance.status_code == 200 and assurance.json["data"]["non_mutating"] is True
    graph = client.get(f"/api/fir/cases/{CASE}/graph")
    assert graph.status_code == 200
    assert graph.json["data"]["derived"] is False
    assert graph.json["data"]["edges"]
    report = client.get(f"/api/fir/cases/{CASE}/report-preview")
    assert report.status_code == 200
    assert report.json["data"]["source_cited"] is True
    assert "SYNTHETIC DATATHON PROTOTYPE" in report.json["data"]["html"]
