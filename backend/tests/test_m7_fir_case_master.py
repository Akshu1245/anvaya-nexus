import sqlite3
import pytest
from backend.anvaya.services.generator import generate
from backend.anvaya.services.investigation import case_360
from backend.anvaya.repositories.search_filter import CaseSearchFilter

def test_case_master_fields_and_fixture(app):
 r=app.extensions["repository"]; generate(r,app.config,"test")
 assert r.schema_version()==15 and r.table_count("cases")==30
 row=r.find_case_360_case("SYN-CASE-0001")
 assert row["case_number"] and row["incident_from_at"] and row["information_received_at"] and row["brief_facts"]
 assert r.search_case_candidates(CaseSearchFilter(crime_number=row["crime_number"],source_system_ids=("CCTNS_REPLICA",)))
 with pytest.raises(sqlite3.IntegrityError): r.connection.execute("UPDATE cases SET latitude=12.0,longitude=NULL WHERE id=?",("SYN-CASE-0001",))
 with pytest.raises(sqlite3.IntegrityError): r.connection.execute("UPDATE cases SET brief_facts='<script>' WHERE id=?",("SYN-CASE-0001",))
 d=case_360(r,r.find_user_by_id("SYN-USR-INV"),"Active Case Investigation","SYN-CASE-0001")
 assert {"INCIDENT_START","INFORMATION_RECEIVED","FIR_REGISTERED"} <= {x["kind"] for x in d["timeline"]}
