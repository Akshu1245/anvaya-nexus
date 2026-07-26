from backend.anvaya.services.generator import generate

PASSWORD="ANVAYA-DEMO-ONLY-2026"
def login(client,user="investigator.demo"):return client.post("/api/auth/login",json={"username":user,"password":PASSWORD})
def create(client,purpose="Active Case Investigation",sources=None):return client.post("/api/investigations",json={"title":"Synthetic M3 Test","purpose":purpose,"selected_sources":sources or ["CCTNS_REPLICA"]})
def plan(identifier="SYN-FIR-000001",limit=25):return {"intent":"SEARCH","filters":{"case_identifier":identifier},"selected_sources":["CCTNS_REPLICA"],"result_limit":limit,"confidence":1,"uncertain_fields":[],"protected_tokens":[identifier],"requires_confirmation":False}

def test_login_create_preview_search_assigned_and_external_masking(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client).json["data"]
    preview=client.post(f"/api/investigations/{inv['id']}/query/preview",json={"query":"Find SYN-FIR-000001"});assert preview.status_code==200
    assigned=client.post(f"/api/investigations/{inv['id']}/search",json=plan()).json["data"]["results"][0];assert assigned["jurisdiction_state"]=="assigned_station" and not assigned["masking"]["applied"]
    external=client.post(f"/api/investigations/{inv['id']}/search",json=plan("SYN-FIR-000002")).json["data"]["results"][0];assert external["jurisdiction_state"]=="external" and external["masking"]["level"]=="EXTERNAL"

def test_analyst_results_masked_and_supervisor_boundary(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client,"analyst.demo");inv=create(client,"Pattern Research").json["data"];result=client.post(f"/api/investigations/{inv['id']}/search",json=plan()).json["data"]["results"][0];assert result["masking"]["level"]=="ANALYST"
    client.post("/api/auth/logout");login(client,"supervisor.demo");assert create(client,"Supervisor Review").status_code==403

def test_unauthorised_source_direct_bypass_denied_and_audited(client,app):
    login(client);response=create(client,sources=["COURT_REPLICA"]);assert response.status_code==403 and response.json["code"]=="SOURCE_DENIED"
    assert app.extensions["repository"].connection.execute("SELECT COUNT(*) FROM audit_events WHERE event_type='PERMISSION_DENIAL'").fetchone()[0]>=1

def test_search_filters_reasons_provenance_limits_and_no_invented_ids(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client).json["data"]
    payload=plan();payload["filters"]={"offence":"CHAIN_SNATCHING","status":"UNRESOLVED"};payload["result_limit"]=1
    response=client.post(f"/api/investigations/{inv['id']}/search",json=payload);data=response.json["data"];assert data["result_count"]<=1
    result=data["results"][0];assert {"offence","status"}<=set(result["match_reasons"]);assert result["source_record_references"][0].startswith("SYN-SR-")
    assert result["id"] in {r[0] for r in app.extensions["repository"].connection.execute("SELECT id FROM cases")}

def test_non_search_execution_and_sql_preview_rejected(client):
    login(client);inv=create(client).json["data"];discover=plan();discover["intent"]="DISCOVER"
    assert client.post(f"/api/investigations/{inv['id']}/search",json=discover).status_code==409
    assert client.post(f"/api/investigations/{inv['id']}/query/preview",json={"query":"SELECT * FROM cases"}).status_code==400

def test_location_date_phone_imei_and_vehicle_filters(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client).json["data"]
    variants=[
      {"location":"SYN-STN-01"},
      {"date_from":"2026-03-01","date_to":"2026-07-11"},
      {"phone":"SYN-PHONE-000001"},
      {"imei":"SYN-IMEI-000000000001"},
      {"vehicle_registration":"SYN-REG-000001"},
    ]
    for filters in variants:
        payload=plan();payload["filters"]=filters;response=client.post(f"/api/investigations/{inv['id']}/search",json=payload)
        assert response.status_code==200 and response.json["data"]["result_count"]>=1

def test_stale_source_disclosed_in_search_warning(client,app):
    generate(app.extensions["repository"],app.config,"test");repo=app.extensions["repository"];repo.connection.execute("UPDATE source_systems SET last_successful_sync='2020-01-01T00:00:00+00:00' WHERE id='CCTNS_REPLICA'");repo.connection.commit();login(client);inv=create(client).json["data"]
    response=client.post(f"/api/investigations/{inv['id']}/search",json=plan());assert any("Stale" in warning for warning in response.json["warnings"])

def test_audit_login_preview_execution_without_query_or_password(client,app):
    generate(app.extensions["repository"],app.config,"test");login(client);inv=create(client).json["data"];client.post(f"/api/investigations/{inv['id']}/query/preview",json={"query":"Find SYN-FIR-000001"});client.post(f"/api/investigations/{inv['id']}/search",json=plan())
    events={r[0] for r in app.extensions["repository"].connection.execute("SELECT event_type FROM audit_events")};assert {"LOGIN","QUERY_PREVIEW","SEARCH_EXECUTION"}<=events
    logs=" ".join(r[0] for r in app.extensions["repository"].connection.execute("SELECT safe_metadata_json FROM audit_events"));assert PASSWORD not in logs and "Find SYN-FIR" not in logs
