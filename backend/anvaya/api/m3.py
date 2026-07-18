from __future__ import annotations
import json,uuid
from datetime import datetime,timezone
from functools import wraps
from flask import Blueprint,current_app,g,make_response,request
from pydantic import ValidationError

from backend.anvaya.api.errors import ApiError
from backend.anvaya.schemas.common import SuccessEnvelope
from backend.anvaya.schemas.query import QueryPlan
from backend.anvaya.services.audit import audit
from backend.anvaya.services.auth import current_user,login,public_user,revoke
from backend.anvaya.services.policy import evaluate
from backend.anvaya.services.query_parser import parse_query
from backend.anvaya.services.search import search_cases
from backend.anvaya.services.source_registry import list_sources
from backend.anvaya.services.investigation import PRESETS, case_360, discover, passport, relationship_path, source_control
from backend.anvaya.services.intelligence import actions, assurance, challenge, dna, graph, verify
from backend.anvaya.services.reports import create as create_report, review as review_report, submit as submit_report, update as update_report, new_version, _report, allowed, listing, assign

m3_blueprint=Blueprint("m3",__name__,url_prefix="/api")
_rate={}
_login_rate={}

def _ok(data,warnings=None,status=200):return SuccessEnvelope[dict|list](request_id=g.request_id,data=data,warnings=warnings or []).model_dump(mode="json"),status
def _token():return request.cookies.get(current_app.config["SESSION_COOKIE_NAME"])
def protected(fn):
 @wraps(fn)
 def wrapper(*args,**kwargs):
  key=f"{id(current_app.extensions['repository'])}:{request.remote_addr or 'local'}";now=datetime.now(timezone.utc).timestamp();hits=[t for t in _rate.get(key,[]) if now-t<60]
  if len(hits)>=120:raise ApiError("RATE_LIMITED","Too many requests.",429,True)
  hits.append(now);_rate[key]=hits;g.user=current_user(current_app.extensions["repository"],_token(),g.request_id);return fn(*args,**kwargs)
 return wrapper

@m3_blueprint.post("/auth/login")
def auth_login():
 key=f"{id(current_app.extensions['repository'])}:{request.remote_addr or 'local'}";now=datetime.now(timezone.utc).timestamp();hits=[t for t in _login_rate.get(key,[]) if now-t<60]
 if len(hits)>=current_app.config["LOGIN_RATE_LIMIT_PER_MINUTE"]:raise ApiError("LOGIN_RATE_LIMITED","Too many login attempts. Try again later.",429,True)
 hits.append(now);_login_rate[key]=hits
 payload=request.get_json(silent=True) or {};token,user=login(current_app.extensions["repository"],str(payload.get("username","")),str(payload.get("password","")),current_app.config["SESSION_TTL_MINUTES"],g.request_id)
 body,status=_ok(user);response=make_response(body,status);response.set_cookie(current_app.config["SESSION_COOKIE_NAME"],token,httponly=True,samesite="Strict",secure=bool(current_app.config["HTTPS_ENABLED"]),max_age=current_app.config["SESSION_TTL_MINUTES"]*60);return response

@m3_blueprint.post("/auth/logout")
@protected
def auth_logout():
 revoke(current_app.extensions["repository"],_token(),g.request_id);body,status=_ok({"logged_out":True});response=make_response(body,status);response.delete_cookie(current_app.config["SESSION_COOKIE_NAME"]);return response

@m3_blueprint.get("/auth/session")
@protected
def session():return _ok(public_user(g.user))

@m3_blueprint.get("/m3/sources")
@protected
def permitted_sources():
 decision=evaluate(g.user,"Supervisor Review" if g.user["role"]=="SUPERVISOR" else ("Pattern Research" if g.user["role"]=="CRIME_ANALYST" else "Active Case Investigation"),[],"REVIEW" if g.user["role"]=="SUPERVISOR" else "SOURCE_LIST",current_app.config["MAX_SEARCH_RESULTS"])
 permitted=set(decision.permitted_sources);return _ok([{**s,"selectable":s["id"] in permitted and s["status"]!="Unavailable"} for s in list_sources(current_app.extensions["repository"])])

@m3_blueprint.post("/investigations")
@protected
def create_investigation():
 payload=request.get_json(silent=True) or {};title=str(payload.get("title","")).strip();purpose=payload.get("purpose");sources=payload.get("selected_sources",[])
 if not title:raise ApiError("TITLE_REQUIRED","Investigation title is required.",400,False)
 decision=evaluate(g.user,purpose,sources,"CREATE_INVESTIGATION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed:audit(current_app.extensions["repository"],"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 iid=f"SYN-INV-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo=current_app.extensions["repository"]
 repo.connection.execute("INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?,?)",(iid,g.user["id"],title,purpose,json.dumps(sources),g.user["assigned_station"],g.user["assigned_district"],now,now));repo.connection.commit();audit(repo,"INVESTIGATION_CREATE","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid});return _ok(_investigation(repo,iid),status=201)

def _investigation(repo,iid):
 row=repo.connection.execute("SELECT * FROM investigations WHERE id=?",(iid,)).fetchone()
 if not row:return None
 result=dict(row);result["selected_sources"]=json.loads(result.pop("selected_sources_json"));return result

@m3_blueprint.get("/investigations")
@protected
def investigations():
 repo=current_app.extensions["repository"];ids=[r[0] for r in repo.connection.execute("SELECT id FROM investigations WHERE user_id=? ORDER BY updated_at DESC",(g.user["id"],))];return _ok([_investigation(repo,i) for i in ids])

@m3_blueprint.get("/investigation-home")
@protected
def investigation_home():
 repo=current_app.extensions["repository"];items=[_investigation(repo,r[0]) for r in repo.connection.execute("SELECT id FROM investigations WHERE user_id=? ORDER BY updated_at DESC LIMIT 10",(g.user["id"],))]
 health=list_sources(repo);degraded=[s for s in health if s["status"]!="Fresh"]
 return _ok({"user":public_user(g.user),"recent_investigations":items,"source_health":health,"degraded_mode":bool(degraded),"degraded_sources":[s["id"] for s in degraded]})

@m3_blueprint.get("/source-control")
@protected
def source_control_centre():
 purpose=request.args.get("purpose") or ("Pattern Research" if g.user["role"]=="CRIME_ANALYST" else "Active Case Investigation")
 return _ok(source_control(current_app.extensions["repository"],g.user,purpose))

@m3_blueprint.get("/investigations/<iid>")
@protected
def investigation(iid):
 repo=current_app.extensions["repository"];item=_investigation(repo,iid)
 if not item or item["user_id"]!=g.user["id"]:raise ApiError("INVESTIGATION_NOT_FOUND","Investigation was not found.",404,False)
 audit(repo,"INVESTIGATION_OPEN","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid});return _ok(item)

def _owned(repo,iid):
 inv=_investigation(repo,iid)
 if not inv or inv["user_id"]!=g.user["id"]:raise ApiError("INVESTIGATION_NOT_FOUND","Investigation was not found.",404,False)
 return inv

@m3_blueprint.patch("/investigations/<iid>/sources")
@protected
def update_sources(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {};sources=payload.get("selected_sources",[])
 decision=evaluate(g.user,inv["purpose"],sources,"SOURCE_SELECTION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed: audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403)
 repo.connection.execute("UPDATE investigations SET selected_sources_json=?,updated_at=? WHERE id=?",(json.dumps(sources),datetime.now(timezone.utc).isoformat(),iid));repo.connection.commit();audit(repo,"SOURCE_SELECTION_CHANGED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"source_count":len(sources)});return _ok(_investigation(repo,iid))

@m3_blueprint.post("/investigations/<iid>/sources/preset")
@protected
def apply_preset(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);preset=(request.get_json(silent=True) or {}).get("preset")
 if preset not in PRESETS:raise ApiError("PRESET_NOT_FOUND","Source preset was not found.",404)
 sources=PRESETS[preset];decision=evaluate(g.user,inv["purpose"],sources,"SOURCE_SELECTION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
 repo.connection.execute("UPDATE investigations SET selected_sources_json=?,updated_at=? WHERE id=?",(json.dumps(sources),datetime.now(timezone.utc).isoformat(),iid));repo.connection.commit();audit(repo,"SOURCE_PRESET_SELECTED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"preset":preset});return _ok(_investigation(repo,iid))

@m3_blueprint.get("/investigations/<iid>/history")
@protected
def history(iid):
 repo=current_app.extensions["repository"];_owned(repo,iid);return _ok([dict(row) for row in repo.connection.execute("SELECT id,original_text,query_plan_json,confirmed,parent_message_id,execution_intent,result_count,request_id,created_at FROM investigation_messages WHERE investigation_id=? ORDER BY created_at",(iid,))])

@m3_blueprint.post("/investigations/<iid>/query/preview")
@protected
def preview(iid):
 repo=current_app.extensions["repository"];inv=_investigation(repo,iid)
 if not inv or inv["user_id"]!=g.user["id"]:raise ApiError("INVESTIGATION_NOT_FOUND","Investigation was not found.",404,False)
 payload=request.get_json(silent=True) or {};plan=parse_query(str(payload.get("query","")),inv["selected_sources"]);decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"SEARCH",plan.result_limit)
 if not decision.allowed:audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 mid=f"SYN-MSG-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo.connection.execute("INSERT INTO investigation_messages (id,investigation_id,original_text,query_plan_json,confirmed,created_at,execution_intent,request_id) VALUES (?,?,?,?,?,?,?,?)",(mid,iid,payload["query"],plan.model_dump_json(),0,now,plan.intent,g.request_id));repo.connection.commit();audit(repo,"QUERY_PREVIEW","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"intent":plan.intent})
 states={s["id"]:s["status"] for s in list_sources(repo)};return _ok({"message_id":mid,"original_query":payload["query"],"normalised_interpretation":plan.model_dump(mode="json"),"policy_preview":decision.dict(),"source_states":states,"warnings":["Confirmation required"] if plan.requires_confirmation else []})

@m3_blueprint.post("/investigations/<iid>/query/follow-up")
@protected
def follow_up(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {};parent=payload.get("parent_message_id")
 previous=repo.connection.execute("SELECT query_plan_json FROM investigation_messages WHERE id=? AND investigation_id=?",(parent,iid)).fetchone()
 if not previous:raise ApiError("CONTEXT_NOT_FOUND","Follow-up context was not found in this investigation.",404)
 plan=parse_query(str(payload.get("query","")),inv["selected_sources"]);old=QueryPlan.model_validate_json(previous["query_plan_json"])
 for field in ("offence","location","date_from","date_to","status"):
  if getattr(plan.filters,field) is None:setattr(plan.filters,field,getattr(old.filters,field))
 plan.selected_sources=old.selected_sources;plan.result_limit=min(plan.result_limit,old.result_limit);plan.protected_tokens=list(dict.fromkeys(old.protected_tokens+plan.protected_tokens))
 mid=f"SYN-MSG-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo.connection.execute("INSERT INTO investigation_messages (id,investigation_id,original_text,query_plan_json,confirmed,created_at,parent_message_id) VALUES (?,?,?,?,?,?,?)",(mid,iid,payload.get("query",""),plan.model_dump_json(),0,now,parent));repo.connection.commit();audit(repo,"FOLLOW_UP_PREVIEW","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"parent":parent});return _ok({"message_id":mid,"parent_message_id":parent,"normalised_interpretation":plan.model_dump(mode="json"),"inherited_fields":[f for f in ("offence","location","date_from","date_to","status") if getattr(old.filters,f) is not None and getattr(plan.filters,f)==getattr(old.filters,f)],"requires_confirmation":plan.requires_confirmation})

def _validated_plan(payload):
 try:return QueryPlan.model_validate(payload)
 except ValidationError as error:raise ApiError("INVALID_QUERY_PLAN","Edited query preview is invalid.",400,False) from error

@m3_blueprint.post("/query/validate")
@protected
def validate_plan():return _ok(_validated_plan(request.get_json(silent=True) or {}).model_dump(mode="json"))

@m3_blueprint.post("/investigations/<iid>/query/<mid>/confirm")
@protected
def confirm(iid,mid):
 plan=_validated_plan(request.get_json(silent=True) or {});repo=current_app.extensions["repository"];row=repo.connection.execute("SELECT * FROM investigation_messages WHERE id=? AND investigation_id=?",(mid,iid)).fetchone()
 if not row:raise ApiError("QUERY_PREVIEW_NOT_FOUND","Query preview was not found.",404,False)
 repo.connection.execute("UPDATE investigation_messages SET query_plan_json=?,confirmed=1 WHERE id=?",(plan.model_dump_json(),mid));repo.connection.commit();return _ok({"message_id":mid,"confirmed":True,"plan":plan.model_dump(mode="json")})

@m3_blueprint.post("/investigations/<iid>/search")
@protected
def execute_search(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 plan=_validated_plan(request.get_json(silent=True) or {})
 if plan.intent!="SEARCH":raise ApiError("INTENT_NOT_AVAILABLE",f"{plan.intent} execution is not available until a later milestone.",409,False)
 decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"SEARCH",plan.result_limit)
 if not decision.allowed:audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 results=search_cases(repo,g.user,inv["purpose"],plan);audit(repo,"SEARCH_EXECUTION","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"result_count":len(results)})
 states={s["id"]:s["status"] for s in list_sources(repo) if s["id"] in plan.selected_sources};warnings=[f"{sid} is {state}" for sid,state in states.items() if state!="Fresh"]
 return _ok({"results":results,"result_count":len(results),"source_states":states,"policy":decision.dict()},warnings)

@m3_blueprint.post("/investigations/<iid>/discover")
@protected
def execute_discover(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);plan=_validated_plan(request.get_json(silent=True) or {})
 if plan.intent!="DISCOVER":raise ApiError("INTENT_REQUIRED","DISCOVER intent is required.",409)
 decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"DISCOVER",plan.result_limit)
 if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
 results=discover(repo,g.user,inv["purpose"],plan);audit(repo,"DISCOVER_EXECUTION","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"result_count":len(results)});return _ok({"results":results,"result_count":len(results),"candidate_only":True})

@m3_blueprint.get("/cases/<case_id>/360")
@protected
def case_review(case_id):
 purpose=request.args.get("purpose","Active Case Investigation");result=case_360(current_app.extensions["repository"],g.user,purpose,case_id);audit(current_app.extensions["repository"],"CASE_360_OPENED","SUCCESS",g.user["id"],g.request_id,{"case_id":case_id});return _ok(result)

@m3_blueprint.get("/source-passports/<source_record_id>")
@protected
def source_passport(source_record_id):
 purpose=request.args.get("purpose","Active Case Investigation");result=passport(current_app.extensions["repository"],g.user,purpose,source_record_id);audit(current_app.extensions["repository"],"SOURCE_PASSPORT_VIEWED","SUCCESS",g.user["id"],g.request_id,{"source_record_id":source_record_id});return _ok(result)

@m3_blueprint.get("/relationships/path")
@protected
def path():
 result=relationship_path(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),request.args.get("from",""),request.args.get("to",""),request.args.get("max_hops",3));audit(current_app.extensions["repository"],"RELATIONSHIP_PATH_REQUESTED","SUCCESS",g.user["id"],g.request_id,{"path_length":len(result["path"])});return _ok(result)

@m3_blueprint.get("/m5/case-dna/<left>/<right>")
@protected
def m5_dna(left,right):
 result=dna(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),left,right);audit(current_app.extensions["repository"],"CASE_DNA_COMPARISON","SUCCESS",g.user["id"],g.request_id,{"score":result["score"]});return _ok(result)
@m3_blueprint.get("/m5/graph/<case_id>")
@protected
def m5_graph(case_id):
 result=graph(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),case_id,request.args.get("hops",3));audit(current_app.extensions["repository"],"EVIDENCE_GRAPH_OPENED","SUCCESS",g.user["id"],g.request_id,{"nodes":len(result["nodes"])});return _ok(result)
@m3_blueprint.get("/m5/assurance/<case_id>")
@protected
def m5_assurance(case_id):return _ok(assurance(current_app.extensions["repository"],case_id))
@m3_blueprint.get("/m5/verify/<left>/<right>")
@protected
def m5_verify(left,right):
 result=verify(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),left,right);audit(current_app.extensions["repository"],"VERIFY_EXECUTED","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
@m3_blueprint.post("/m5/challenge/<case_id>")
@protected
def m5_challenge(case_id):
 result=challenge(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),case_id,str((request.get_json(silent=True) or {}).get("hypothesis","")));audit(current_app.extensions["repository"],"HYPOTHESIS_CHALLENGE","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
@m3_blueprint.get("/m5/actions/<case_id>")
@protected
def m5_actions(case_id):
 result=actions(current_app.extensions["repository"],g.user,request.args.get("purpose","Active Case Investigation"),case_id);audit(current_app.extensions["repository"],"ACTION_IMPACT_PREVIEW","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
@m3_blueprint.post('/reports')
@protected
def reports_create():
 result=create_report(current_app.extensions['repository'],g.user,request.get_json(silent=True) or {});audit(current_app.extensions['repository'],'REPORT_DRAFT_CREATED','SUCCESS',g.user['id'],g.request_id,{'report_id':result['report_id']});return _ok(result, status=201)
@m3_blueprint.get('/reports')
@protected
def reports_list():
 limit=min(max(int(request.args.get('limit',25)),1),50);offset=max(int(request.args.get('offset',0)),0);return _ok({'reports':listing(current_app.extensions['repository'],g.user,limit,offset),'limit':limit,'offset':offset})
@m3_blueprint.get('/reports/<rid>')
@protected
def reports_detail(rid):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 v=repo.connection.execute("SELECT * FROM report_versions WHERE report_id=? ORDER BY version_number DESC",(rid,)).fetchall();history=[dict(x) for x in repo.connection.execute("SELECT rr.decision,rr.note,rr.created_at,u.username FROM report_reviews rr JOIN users u ON u.id=rr.reviewer_user_id WHERE rr.report_version_id IN (SELECT id FROM report_versions WHERE report_id=?) ORDER BY rr.created_at",(rid,))];return _ok({'report':r,'versions':[dict(x) for x in v],'review_history':history,'allowed_actions':['review'] if g.user['role']=='SUPERVISOR' else ['update','submit']})
@m3_blueprint.get('/reports/<rid>/versions/<int:number>')
@protected
def reports_version(rid,number):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 row=repo.connection.execute("SELECT id,version_number,status,sections_json,notes,created_by,created_at,immutable FROM report_versions WHERE report_id=? AND version_number=?",(rid,number)).fetchone()
 if not row:raise ApiError('VERSION_NOT_FOUND','Report version was not found.',404)
 return _ok(dict(row))
@m3_blueprint.get('/reviewers')
@protected
def reviewers():
 return _ok([dict(x) for x in current_app.extensions['repository'].connection.execute("SELECT username,role FROM users WHERE role='SUPERVISOR' AND active=1")])
@m3_blueprint.post('/reports/<rid>/assign')
@protected
def reports_assign(rid):
 result=assign(current_app.extensions['repository'],g.user,rid,str((request.get_json(silent=True) or {}).get('reviewer','')));audit(current_app.extensions['repository'],'REVIEW_ASSIGNED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok(result)
@m3_blueprint.post('/reports/<rid>/submit')
@protected
def reports_submit(rid):
 result=submit_report(current_app.extensions['repository'],g.user,rid);audit(current_app.extensions['repository'],'REPORT_SUBMITTED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok(result)
@m3_blueprint.patch('/reports/<rid>')
@protected
def reports_update(rid):
 result=update_report(current_app.extensions['repository'],g.user,rid,request.get_json(silent=True) or {});audit(current_app.extensions['repository'],'REPORT_DRAFT_UPDATED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok(result)
@m3_blueprint.post('/reports/<rid>/versions')
@protected
def reports_new_version(rid):return _ok(new_version(current_app.extensions['repository'],g.user,rid))
@m3_blueprint.get('/reports/<rid>/preview')
@protected
def reports_preview(rid):
 row=current_app.extensions['repository'].connection.execute("SELECT rv.html,r.owner_user_id FROM reports r JOIN report_versions rv ON rv.report_id=r.id AND rv.version_number=r.current_version WHERE r.id=?",(rid,)).fetchone()
 if not row or (row['owner_user_id']!=g.user['id'] and g.user['role']!='SUPERVISOR'):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 audit(current_app.extensions['repository'],'REPORT_PREVIEW_GENERATED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok({'report_id':rid,'html':row['html'],'export':'browser-print-to-PDF'})
@m3_blueprint.get('/reports/<rid>/preview-metadata')
@protected
def reports_preview_metadata(rid):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 v=repo.connection.execute("SELECT * FROM report_versions WHERE report_id=? AND version_number=?",(rid,r['current_version'])).fetchone();reviewer=repo.connection.execute("SELECT username FROM users WHERE id=?",(r['assigned_reviewer_id'],)).fetchone()
 return _ok({'report_id':rid,'title':r['title'],'version_number':v['version_number'],'status':r['status'],'generated_by':v['created_by'],'reviewed_by':reviewer['username'] if reviewer else None,'generated_timestamp':v['created_at'],'selected_sections':json.loads(v['sections_json']),'masking_notices':['Masking remains policy-filtered.'],'jurisdiction_notices':['Jurisdiction is re-evaluated at access time.'],'stale_source_warnings':[],'unavailable_source_warnings':['Court and Prosecution are unavailable P1 metadata.'],'missing_provenance_warnings':['Missing provenance is disclosed where seeded.'],'provenance_summary':{'count':0,'safe':'Source-backed references are retained in the report.'},'filename':f"anvaya-{rid.lower()}-v{v['version_number']}.html",'native_pdf_available':False,'browser_print_to_pdf_available':True,'allowed_actions':['review'] if g.user['role']=='SUPERVISOR' else ['preview','submit']})
@m3_blueprint.post('/reports/<rid>/review')
@protected
def reports_review(rid):
 p=request.get_json(silent=True) or {};result=review_report(current_app.extensions['repository'],g.user,rid,str(p.get('decision','')),str(p.get('note','')));audit(current_app.extensions['repository'],'REPORT_REVIEWED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid,'decision':result['status']});return _ok(result)
@m3_blueprint.get('/system-health')
@protected
def system_health():
 repo=current_app.extensions['repository'];sources=list_sources(repo);return _ok({'backend':'ok','database':repo.health_check(),'migration_version':4,'frontend_build':'M6 local build','sources':sources,'optional_ai':'disabled','report_export':'browser-print-to-PDF','degraded_mode':any(s['status']!='Fresh' for s in sources),'degraded_reasons':[f"{source['name']} is {source['status']}" for source in sources if source['status']!='Fresh'],'warnings':['Synthetic source limitations remain visible in all results.']})
@m3_blueprint.get('/audit-events')
@protected
def audit_events():
 repo=current_app.extensions['repository'];p=request.args;limit=min(max(int(p.get('limit',25)),1),50);offset=max(int(p.get('offset',0)),0);where=[];args=[]
 if g.user['role']!='SUPERVISOR': where.append("user_id=?");args.append(g.user['id'])
 for key,col in (('event_type','event_type'),('outcome','outcome'),('request_id','request_id')):
  if p.get(key):where.append(f'{col}=?');args.append(p[key])
 for key,op in (('start','>='),('end','<=')):
  if p.get(key):
   try:datetime.fromisoformat(p[key].replace('Z','+00:00'))
   except ValueError:raise ApiError('INVALID_AUDIT_DATE','Audit dates must be ISO timestamps.',400)
   where.append(f'occurred_at {op} ?');args.append(p[key])
 if p.get('actor_role') and p['actor_role'] not in {'INVESTIGATOR','CRIME_ANALYST','SUPERVISOR'}:raise ApiError('INVALID_AUDIT_ROLE','Audit role is invalid.',400)
 if p.get('actor_role'):
  where.append("user_id IN (SELECT id FROM users WHERE role=?)");args.append(p['actor_role'])
 for key in ('investigation','report'):
  if p.get(key):
   value=p[key]
   if not value.startswith('SYN-INV-' if key=='investigation' else 'SYN-RPT-'):raise ApiError('INVALID_AUDIT_REFERENCE','Audit reference is invalid.',400)
   where.append("safe_metadata_json LIKE ?");args.append('%'+value+'%')
 if p.get('start') and p.get('end') and p['start']>p['end']:raise ApiError('INVALID_AUDIT_RANGE','Audit start must be before end.',400)
 sql='SELECT id,user_id,event_type,outcome,request_id,safe_metadata_json,occurred_at FROM audit_events'+(' WHERE '+' AND '.join(where) if where else '')+' ORDER BY occurred_at DESC LIMIT ? OFFSET ?';rows=[dict(x) for x in repo.connection.execute(sql,(*args,limit,offset))]
 audit(repo,'AUDIT_DASHBOARD_VIEWED','SUCCESS',g.user['id'],g.request_id,{'count':len(rows)});return _ok({'events':rows,'limit':limit,'offset':offset})
