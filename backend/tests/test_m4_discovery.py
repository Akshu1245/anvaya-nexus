from backend.anvaya.services.generator import generate

PASSWORD="ANVAYA-DEMO-ONLY-2026"
def login(client,user="investigator.demo"):
    return client.post("/api/auth/login",json={"username":user,"password":PASSWORD})
def create(client):
    return client.post("/api/investigations",json={"title":"M4 test","purpose":"Active Case Investigation","selected_sources":["CCTNS_REPLICA","FORENSICS_REPLICA","VEHICLE_REPLICA"]}).json["data"]
def plan():
    return {"intent":"DISCOVER","filters":{"case_identifier":"SYN-FIR-000001"},"selected_sources":["CCTNS_REPLICA"],"result_limit":25,"confidence":1,"uncertain_fields":[],"protected_tokens":["SYN-FIR-000001"],"requires_confirmation":False}

def test_home_source_control_and_preset(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client)
    assert client.get("/api/investigation-home").status_code==200
    sources=client.get("/api/source-control?purpose=Active%20Case%20Investigation").json["data"]["sources"]
    assert any(x["id"]=="COURT_REPLICA" and not x["selectable"] for x in sources)
    inv=create(client);response=client.post(f"/api/investigations/{inv['id']}/sources/preset",json={"preset":"Vehicle Verification"})
    assert response.status_code==200 and "VEHICLE_REPLICA" in response.json["data"]["selected_sources"]

def test_followup_discover_case360_passport_and_path(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client)
    first=client.post(f"/api/investigations/{inv['id']}/query/preview",json={"query":"Find SYN-FIR-000001"}).json["data"]
    follow=client.post(f"/api/investigations/{inv['id']}/query/follow-up",json={"parent_message_id":first["message_id"],"query":"Phone, IMEI athava vehicle connection iruva cases matra."})
    assert follow.status_code==200 and follow.json["data"]["parent_message_id"]==first["message_id"]
    result=client.post(f"/api/investigations/{inv['id']}/discover",json=plan())
    assert result.status_code==200 and result.json["data"]["candidate_only"]
    case=client.get("/api/cases/SYN-CASE-0001/360?purpose=Active%20Case%20Investigation");assert case.status_code==200 and "trust_issues" in case.json["data"]
    source_id=case.json["data"]["overview"]["source_record_references"][0]
    assert client.get(f"/api/source-passports/{source_id}?purpose=Active%20Case%20Investigation").status_code==200
    assert client.get("/api/relationships/path?purpose=Active%20Case%20Investigation&from=SYN-CASE-0001&to=SYN-CASE-0002").status_code==200

def test_cross_user_and_masked_passport_denied_or_masked(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client);client.post("/api/auth/logout");login(client,"analyst.demo")
    assert client.get(f"/api/investigations/{inv['id']}").status_code==404
    response=client.get("/api/source-passports/SYN-SR-CCTNS_REPLICA-SYN-CASE-0002",query_string={"purpose":"Pattern Research"})
    assert response.status_code==200 and response.json["data"]["masking_state"]["level"]=="ANALYST"
