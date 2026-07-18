from backend.anvaya.services.official_fir import seed_official_fir_fixture


def login(client):
    response = client.post("/api/auth/login", json={"username": "analyst.demo", "password": "ANVAYA-DEMO-ONLY-2026"})
    assert response.status_code == 200


def test_official_fir_schema_and_fixture_are_ready(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)
    response = client.get("/api/fir/readiness")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["schema_version"] == 5
    assert data["synthetic_only"] is True
    assert data["counts"]["fir_case_details"] == 24
    assert data["counts"]["case_person_roles"] >= 40


def test_search_by_person_role_and_legal_section(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)
    response = client.get("/api/fir/cases?person_name=Accused%20Alpha&role=ACCUSED&section=303")
    assert response.status_code == 200
    results = response.get_json()["data"]["results"]
    assert [item["id"] for item in results] == ["FIR-CASE-0001"]


def test_search_supports_full_record_retrieval(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)
    response = client.get("/api/fir/cases?q=Kavya&act=IT_ACT&status=UNDER_INVESTIGATION")
    assert response.status_code == 200
    assert {item["id"] for item in response.get_json()["data"]["results"]} == {
        "FIR-CASE-0005", "FIR-CASE-0006", "FIR-CASE-0021"
    }
    response = client.get("/api/fir/cases?category=UDR&minor_head=UNNATURAL_DEATH")
    assert response.status_code == 200
    assert {item["id"] for item in response.get_json()["data"]["results"]} == {"FIR-CASE-0010", "FIR-CASE-0022"}


def test_official_case_360_contains_dataset_sections(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)
    response = client.get("/api/fir/cases/FIR-CASE-0002/360")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["case"]["case_category_code"] == "FIR"
    assert {p["role_type"] for p in data["people"]} == {"ACCUSED", "COMPLAINANT"}
    assert data["legal_sections"][0]["section_code"] == "309"
    assert data["arrest_surrender_events"][0]["event_type"] == "ARREST"
    assert data["related_cases"][0]["case_id"] == "FIR-CASE-0001"


def test_invalid_person_role_is_rejected(client, app):
    seed_official_fir_fixture(app.extensions["repository"])
    login(client)
    response = client.get("/api/fir/cases?role=WITNESS")
    assert response.status_code == 400
    assert response.get_json()["code"] == "INVALID_PERSON_ROLE"
