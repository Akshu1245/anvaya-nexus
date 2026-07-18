import io
import json

VALID={"external_id":"SYN-IMPORT-CASE-001","fir_number":"SYN-FIR-IMPORT-001","crime_number":"SYN-CRIME-IMPORT-001","station_id":"SYN-STN-01","district_id":"SYN-DST-01","offence":"CHAIN_SNATCHING","incident_at":"2026-07-01T10:00:00+00:00","registered_at":"2026-07-01T12:00:00+00:00","status":"UNRESOLVED"}


def upload(client,content,name): return client.post("/api/imports/validate",data={"file":(io.BytesIO(content),name)},content_type="multipart/form-data")


def test_csv_validate_only_then_commit(client,app):
    header=','.join(VALID); row=','.join(VALID.values()); response=upload(client,f"{header}\n{row}\n".encode(),"synthetic.csv")
    assert response.status_code==201; job=response.json["data"]; assert job["accepted_count"]==1 and job["status"]=="VALIDATED"
    assert app.extensions["repository"].table_count("cases")==0
    committed=client.post(f"/api/imports/{job['id']}/commit"); assert committed.status_code==200
    assert committed.json["data"]["status"]=="COMMITTED"; assert app.extensions["repository"].table_count("cases")==1


def test_json_validate_to_commit(client,app):
    row=dict(VALID,external_id="SYN-IMPORT-CASE-JSON",fir_number="SYN-FIR-JSON",crime_number="SYN-CRIME-JSON")
    response=upload(client,json.dumps([row]).encode(),"synthetic.json"); job=response.json["data"]
    assert job["accepted_count"]==1; client.post(f"/api/imports/{job['id']}/commit")
    assert app.extensions["repository"].connection.execute("SELECT COUNT(*) FROM cases WHERE id=?",(row["external_id"],)).fetchone()[0]==1


def test_invalid_rows_are_quarantined_and_never_committed(client,app):
    bad_missing={"external_id":"SYN-BAD-MISSING"}; bad_date=dict(VALID,external_id="SYN-BAD-DATE",incident_at="not-a-date"); dup1=dict(VALID,external_id="SYN-DUP"); dup2=dict(VALID,external_id="SYN-DUP",fir_number="SYN-FIR-DUP2"); orphan=dict(VALID,external_id="SYN-ORPHAN",document_id="SYN-DOC",document_case_id="SYN-OTHER")
    response=upload(client,json.dumps([bad_missing,bad_date,dup1,dup2,orphan]).encode(),"bad.json"); job=response.json["data"]
    categories={f["category"] for f in job["failures"]}
    assert {"missing_required_key","invalid_date","duplicate_identifier","unlinked_document"}<=categories
    assert job["accepted_count"]==1 and job["failed_count"]>=4
    client.post(f"/api/imports/{job['id']}/commit")
    assert app.extensions["repository"].connection.execute("SELECT COUNT(*) FROM cases WHERE id LIKE 'SYN-BAD-%' OR id='SYN-ORPHAN'").fetchone()[0]==0


def test_import_checksum_and_job_inspection(client):
    response=upload(client,json.dumps([VALID]).encode(),"check.json"); job=response.json["data"]
    assert len(job["checksum"])==64 and job["source_version"]=="synthetic-import-1.0"
    inspected=client.get(f"/api/imports/{job['id']}"); assert inspected.json["data"]["checksum"]==job["checksum"]


def test_validation_failure_contract(client):
    response=upload(client,b"not json","bad.json"); assert response.status_code==400
    assert response.json["code"]=="INVALID_IMPORT_FILE"
