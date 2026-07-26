"""Offline fake-client coverage for fixed M6 report read projections."""
from __future__ import annotations
import pytest
from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.catalyst_gateway import CatalystReadGateway
from backend.anvaya.repositories.catalyst_readonly import CatalystReadOnlyRepository
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName
from backend.tests.fakes.fake_catalyst_client import FakeCatalystClient

R, U, S = "SYN-RPT-1", "SYN-USR-INV", "SYN-USR-SUP"
def report(**x):
 r={"ROWID":"r","id":R,"investigation_id":"SYN-INV-1","owner_user_id":U,"assigned_reviewer_id":S,"title":"Synthetic","status":"DRAFT","current_version":"1","created_at":"2026-01-01T00:00:00+00:00","updated_at":"2026-01-02T00:00:00+00:00","owner_name":"investigator.demo","reviewer_name":"supervisor.demo"};r.update(x);return r
def version(**x):
 r={"ROWID":"v","id":"SYN-RV-1","report_id":R,"version_number":"1","status":"DRAFT","sections_json":"[\"Cover\"]","notes":"safe","html":"<h1>synthetic</h1>","created_by":U,"created_at":"2026-01-01T00:00:00+00:00","immutable":"0"};r.update(x);return r
@pytest.fixture()
def fake(): return FakeCatalystClient()
@pytest.fixture()
def repo(fake): return CatalystReadOnlyRepository(CatalystReadGateway(fake),fake)

def test_report_lists_versions_and_scope_validation(fake,repo):
 fake.register_rows(CatalystQueryName.REPORT_BY_ID.value,[{k:v for k,v in report().items() if k not in {"owner_name","reviewer_name"}}]);assert repo.find_report(R)["current_version"]==1
 fake.register_rows(CatalystQueryName.REPORTS_BY_OWNER.value,[report()]);assert repo.list_reports_owned_by(U,25,0)[0]["id"]==R
 fake.register_rows(CatalystQueryName.REPORTS_BY_REVIEWER.value,[report()]);assert repo.list_reports_assigned_to(S,25,0)[0]["id"]==R
 fake.register_rows(CatalystQueryName.REPORT_VERSION_BY_NUMBER.value,[version(html="x"*20000,sections_json="[1]"*1000)]);v=repo.find_report_version(R,1);assert isinstance(v["html"],str) and len(v["html"])==20000
 fake.register_rows(CatalystQueryName.REPORT_VERSIONS.value,[version(version_number="2",id="SYN-RV-2"),version()]);assert [v["version_number"] for v in repo.list_report_versions(R)]==[2,1]
 fake.register_rows(CatalystQueryName.REPORTS_BY_OWNER.value,[report(owner_user_id="SYN-USR-X")]);
 with pytest.raises(ApiError): repo.list_reports_owned_by(U,25,0)
 with pytest.raises(ApiError): repo.find_report_version(R,False)

def test_supervisors_history_errors_and_writes_remain_unavailable(fake,repo):
 fake.register_rows(CatalystQueryName.ELIGIBLE_SUPERVISOR_BY_USERNAME.value,[{"ROWID":"s","id":S,"username":"supervisor.demo","role":"SUPERVISOR"}]);assert repo.find_eligible_supervisor("supervisor.demo")["id"]==S
 fake.register_rows(CatalystQueryName.ELIGIBLE_SUPERVISORS.value,[{"username":"z","role":"SUPERVISOR"},{"username":"a","role":"SUPERVISOR"}]);assert [x["username"] for x in repo.list_eligible_supervisors()]==["a","z"]
 fake.register_rows(CatalystQueryName.REPORT_REVIEW_HISTORY.value,[{"decision":"APPROVED","note":"","created_at":"2026-01-01T00:00:00+00:00","username":"supervisor.demo","version_number":"1"}]);assert repo.list_report_review_history(R)[0]["version_number"]==1
 fake.fail(CatalystQueryName.REPORT_BY_ID.value,"timeout",True)
 with pytest.raises(ApiError) as e: repo.find_report(R)
 assert e.value.code=="CATALYST_TIMEOUT"
 for method,args in (("create_report_with_initial_version",({},{})),("assign_report_reviewer",(R,S,"x")),("update_report_draft",(R,1,"t","[]","n","h","x")),("submit_report_version",(R,1,"x")),("create_next_report_draft",(R,1,{},"x")),("create_report_review_decision",(R,1,{},"x"))):
  with pytest.raises(ApiError) as err:getattr(repo,method)(*args)
  assert err.value.code=="CATALYST_NOT_IMPLEMENTED"
