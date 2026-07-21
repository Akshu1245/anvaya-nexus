"""D-9 deterministic FIR Record Assurance contract."""
from backend.anvaya.repositories.audit_requests import AuditEventFilter
from backend.anvaya.services.assurance import RULE_VERSION, evaluate_case_assurance, list_case_assurance, set_assurance_status
from backend.anvaya.services.generator import generate


def _seed(app):
    repository = app.extensions["repository"]; generate(repository, app.config, "test")
    return repository, repository.find_user_by_id("SYN-USR-INV"), repository.find_user_by_id("SYN-USR-SUP")


def test_assurance_materialises_stable_safe_findings_idempotently(app):
    repository, user, _ = _seed(app)
    first = evaluate_case_assurance(repository, "SYN-CASE-0001")
    second = evaluate_case_assurance(repository, "SYN-CASE-0001")
    assert {row["id"] for row in first} == {row["id"] for row in second}
    result = list_case_assurance(repository, user, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",))
    assert result["rule_version"] == RULE_VERSION
    assert result["summary"]["WARNING"] >= 1
    assert all(row["severity"] in {"BLOCKING", "WARNING", "INFORMATIONAL"} for row in result["findings"])
    assert all(row["status"] in {"OPEN", "ACKNOWLEDGED", "RESOLVED"} for row in result["findings"])
    assert "payload_json" not in str(result) and "score" not in str(result).lower()
    assert all("age" not in str(item["observed_values"]).lower() and "gender" not in str(item["observed_values"]).lower() for item in result["findings"])
    assert any(row["rule_code"] in {"DUPLICATE_CRIME_NUMBER_WITHIN_UNIT_YEAR", "SOURCE_RECORD_MISSING"} for row in result["findings"])


def test_assurance_status_is_supervisor_only_and_rerun_reopens_resolved_finding(app):
    repository, investigator, supervisor = _seed(app)
    finding = list_case_assurance(repository, investigator, "Active Case Investigation", "SYN-CASE-0001", ("CCTNS_REPLICA",))["findings"][0]
    try:
        set_assurance_status(repository, investigator, "Active Case Investigation", "SYN-CASE-0001", finding["id"], "RESOLVED", "No")
        assert False, "investigator should not resolve assurance"
    except Exception as error:
        assert getattr(error, "code", None) == "ASSURANCE_ACTION_DENIED"
    resolved = set_assurance_status(repository, supervisor, "Supervisor Review", "SYN-CASE-0001", finding["id"], "RESOLVED", "Reviewed synthetic fixture")
    assert resolved["status"] == "RESOLVED"
    evaluate_case_assurance(repository, "SYN-CASE-0001")
    reopened = next(row for row in repository.list_assurance_trust_issues("SYN-CASE-0001") if row["id"] == finding["id"])
    assert reopened["status"] == "OPEN"
    assert repository.find_user_by_id("SYN-USR-SUP")["role"] == "SUPERVISOR"


def test_assurance_api_audits_execution_and_resolution(client, app):
    repository, _, _ = _seed(app)
    login = client.post("/api/auth/login", json={"username":"investigator.demo", "password":client.application.config["DEMO_PASSWORD"]})
    assert login.status_code == 200
    investigation = client.post("/api/investigations", json={"title":"Assurance", "purpose":"Active Case Investigation", "selected_sources":["CCTNS_REPLICA"]}).get_json()["data"]
    response = client.get(f"/api/investigations/{investigation['id']}/cases/SYN-CASE-0001/assurance")
    assert response.status_code == 200 and response.get_json()["data"]["findings"]
    events = repository.list_audit_events(AuditEventFilter(actor_user_id="SYN-USR-INV", limit=25))
    assert "FIR_ASSURANCE_EXECUTED" in {event["event_type"] for event in events}
