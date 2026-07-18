from datetime import datetime,timedelta,timezone

from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate

PASSWORD="ANVAYA-DEMO-ONLY-2026"
def login(client,username="investigator.demo",password=PASSWORD):return client.post("/api/auth/login",json={"username":username,"password":password,"role":"SUPERVISOR"})

def test_valid_login_session_and_client_role_ignored(client):
    response=login(client);assert response.status_code==200;assert response.json["data"]["role"]=="INVESTIGATOR";assert "HttpOnly" in response.headers["Set-Cookie"]
    assert client.get("/api/auth/session").json["data"]["role"]=="INVESTIGATOR"

def test_invalid_login_and_no_password_audit(client,app):
    response=login(client,password="wrong");assert response.status_code==401
    payload=app.extensions["repository"].connection.execute("SELECT safe_metadata_json FROM audit_events WHERE event_type='LOGIN' ORDER BY occurred_at DESC LIMIT 1").fetchone()[0]
    assert "wrong" not in payload and "password" not in payload

def test_missing_logout_and_revoked_session(client):
    assert client.get("/api/auth/session").status_code==401
    login(client);assert client.post("/api/auth/logout").status_code==200;assert client.get("/api/auth/session").status_code==401

def test_expired_session(client,app):
    login(client);app.extensions["repository"].connection.execute("UPDATE sessions SET expires_at=?",((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),));app.extensions["repository"].connection.commit()
    response=client.get("/api/auth/session");assert response.status_code==401 and response.json["code"]=="SESSION_EXPIRED"

def test_policy_role_purpose_source_and_limits(app):
    repo=app.extensions["repository"];inv=repo.connection.execute("SELECT * FROM users WHERE role='INVESTIGATOR'").fetchone();analyst=repo.connection.execute("SELECT * FROM users WHERE role='CRIME_ANALYST'").fetchone();sup=repo.connection.execute("SELECT * FROM users WHERE role='SUPERVISOR'").fetchone()
    assert evaluate(inv,"Active Case Investigation",["CCTNS_REPLICA"],"SEARCH",999).row_limit==25
    assert evaluate(analyst,"Pattern Research",["CCTNS_REPLICA"],"SEARCH").masking_level=="ANALYST"
    assert not evaluate(sup,"Supervisor Review",[],"SEARCH").allowed
    assert evaluate(sup,"Supervisor Review",[],"REVIEW").allowed
    assert not evaluate(inv,"Supervisor Review",["CCTNS_REPLICA"],"SEARCH").allowed
    assert not evaluate(inv,"Active Case Investigation",["COURT_REPLICA"],"SEARCH").allowed
    assert evaluate(inv,"Active Case Investigation",["CCTNS_REPLICA"],"SEARCH",record_station="SYN-STN-01",record_district="SYN-DST-01").masking_level=="NONE"
    assert evaluate(inv,"Active Case Investigation",["CCTNS_REPLICA"],"SEARCH",record_station="SYN-STN-02",record_district="SYN-DST-01").masking_level=="DISTRICT"
    assert evaluate(inv,"Active Case Investigation",["CCTNS_REPLICA"],"SEARCH",record_station="SYN-STN-02",record_district="SYN-DST-02").masking_level=="EXTERNAL"

def test_all_sensitive_fields_masked_and_metadata_preserved():
    source={"person_name":"Synthetic Person 0001","phone":"SYN-PHONE-123456","imei":"SYN-IMEI-123456789012","vehicle_registration":"SYN-REG-123456","address":"Synthetic Address Full","locality":"Synthetic Locality","sensitive_evidence_reference":"SYN-EVD-SECRET","evidence_type":"DEVICE","evidence_status":"AVAILABLE"}
    result=mask_case(source,"EXTERNAL");serialized=str(result)
    for raw in (source["person_name"],source["phone"],source["imei"],source["vehicle_registration"],source["address"],source["sensitive_evidence_reference"]):assert raw not in serialized
    assert set(result["masking"]["fields"])=={"person_name","phone","imei","vehicle_registration","address","sensitive_evidence_reference"}

def test_protected_source_endpoint_requires_auth_and_disables_p1(client):
    assert client.get("/api/m3/sources").status_code==401;login(client);sources=client.get("/api/m3/sources").json["data"]
    assert all(not s["selectable"] for s in sources if s["id"] in {"COURT_REPLICA","PROSECUTION_REPLICA"})
