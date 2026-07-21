from __future__ import annotations
import json,uuid
from datetime import datetime,timezone
from functools import wraps
from flask import Blueprint,current_app,g,make_response,request,send_file
from io import BytesIO
from pydantic import ValidationError

from backend.anvaya.api.errors import ApiError
from backend.anvaya.schemas.common import SuccessEnvelope
from backend.anvaya.schemas.query import QueryPlan
from backend.anvaya.services.audit import audit, list_events
from backend.anvaya.services.auth import current_user,login,public_user,revoke
from backend.anvaya.services.policy import evaluate
from backend.anvaya.config import ai_assist_enabled
from backend.anvaya.services.llm import llm_answer, llm_interpret, templated_answer
from backend.anvaya.services.query_parser import apply_protected_tokens, extract_protected_tokens, guard_query_text, parse_query
from backend.anvaya.services.search import search_cases
from backend.anvaya.services.source_registry import list_sources
from backend.anvaya.services.investigation import PRESETS, case_360, discover, fir_relationship_graph, fir_relationship_path, passport, related_cases, relationship_path, source_control
from backend.anvaya.services.intelligence import actions, challenge, dna, graph, verify
from backend.anvaya.services.assurance import list_case_assurance, set_assurance_status
from backend.anvaya.services.briefs import grounded_brief
from backend.anvaya.services.brief_pdf import grounded_brief_pdf
from backend.anvaya.services.reports import create as create_report, review as review_report, submit as submit_report, update as update_report, new_version, _report, allowed, listing, assign
from backend.anvaya.services.trends import aggregate_crime_trends
from backend.anvaya.services.briefing import build_shift_briefing
from backend.anvaya.services.compare import compare_cases, verification_priorities
from backend.anvaya.services.chat_actions import resolve_chat_action
from backend.anvaya.services.conversation_pdf import conversation_pdf
from backend.anvaya.services.network_clusters import candidate_network_clusters

m3_blueprint=Blueprint("m3",__name__,url_prefix="/api")
_rate={}
_login_rate={}

def _ok(data,warnings=None,status=200):return SuccessEnvelope[dict|list](request_id=g.request_id,data=data,warnings=warnings or []).model_dump(mode="json"),status
def _token():return request.cookies.get(current_app.config["SESSION_COOKIE_NAME"])
def _source_snapshot(sources):return list(dict.fromkeys(sources))
def _history_label(plan):return f"{plan.intent} · " + ", ".join(key.replace("_"," ") for key,value in plan.filters.model_dump().items() if value is not None)

def _interpret_plan(text:str,sources:list[str]):
 guard_query_text(text)
 protected=extract_protected_tokens(text)
 engine="deterministic"
 plan=None
 if ai_assist_enabled(current_app.config):
  plan=llm_interpret(text,sources,current_app.config)
  if plan is not None:engine="ai_assisted"
 if plan is None:plan=parse_query(text,sources)
 plan=apply_protected_tokens(plan,protected)
 return plan,engine
def _check_login_rate():
 key=f"{id(current_app.extensions['repository'])}:{request.remote_addr or 'local'}";now=datetime.now(timezone.utc).timestamp();hits=[t for t in _login_rate.get(key,[]) if now-t<60]
 if len(hits)>=current_app.config["LOGIN_RATE_LIMIT_PER_MINUTE"]:raise ApiError("LOGIN_RATE_LIMITED","Too many login attempts. Try again later.",429,True)
 hits.append(now);_login_rate[key]=hits
def protected(fn):
 @wraps(fn)
 def wrapper(*args,**kwargs):
  key=f"{id(current_app.extensions['repository'])}:{request.remote_addr or 'local'}";now=datetime.now(timezone.utc).timestamp();hits=[t for t in _rate.get(key,[]) if now-t<60]
  if len(hits)>=120:raise ApiError("RATE_LIMITED","Too many requests.",429,True)
  hits.append(now);_rate[key]=hits;g.user=current_user(current_app.extensions["repository"],_token(),g.request_id);return fn(*args,**kwargs)
 return wrapper

@m3_blueprint.post("/auth/login")
def auth_login():
 _check_login_rate()
 payload=request.get_json(silent=True) or {};token,user=login(current_app.extensions["repository"],str(payload.get("username","")),str(payload.get("password","")),current_app.config["SESSION_TTL_MINUTES"],g.request_id)
 body,status=_ok(user);response=make_response(body,status);response.set_cookie(current_app.config["SESSION_COOKIE_NAME"],token,httponly=True,samesite="Strict",secure=bool(current_app.config["HTTPS_ENABLED"]),max_age=current_app.config["SESSION_TTL_MINUTES"]*60);return response

@m3_blueprint.post("/auth/public-demo")
def auth_public_demo():
 if not current_app.config.get("PUBLIC_DEMO_MODE"):
  raise ApiError("PUBLIC_DEMO_DISABLED","Public demo access is not enabled for this deployment.",404,False)
 _check_login_rate()
 token,user=login(current_app.extensions["repository"],"investigator.demo",current_app.config["DEMO_PASSWORD"],current_app.config["SESSION_TTL_MINUTES"],g.request_id)
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
 payload=request.get_json(silent=True) or {};title=str(payload.get("title","")).strip();purpose=payload.get("purpose");sources=_source_snapshot(payload.get("selected_sources",[]))
 if not title:raise ApiError("TITLE_REQUIRED","Investigation title is required.",400,False)
 decision=evaluate(g.user,purpose,sources,"CREATE_INVESTIGATION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed:audit(current_app.extensions["repository"],"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 iid=f"SYN-INV-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo=current_app.extensions["repository"]
 repo.create_investigation({"id":iid,"user_id":g.user["id"],"title":title,"purpose":purpose,"selected_sources_json":json.dumps(sources),"assigned_station":g.user["assigned_station"],"assigned_district":g.user["assigned_district"],"created_at":now,"updated_at":now});audit(repo,"INVESTIGATION_CREATE","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid});return _ok(_investigation(repo,iid),status=201)

def _investigation(repo,iid):
 row=repo.find_investigation(iid)
 if not row:return None
 return _normalise_investigation(row)

def _normalise_investigation(row):
 result=dict(row);result["selected_sources"]=json.loads(result.pop("selected_sources_json"));return result

@m3_blueprint.get("/investigations")
@protected
def investigations():
 repo=current_app.extensions["repository"];return _ok([_normalise_investigation(item) for item in repo.list_investigations_for_user(g.user["id"])])

@m3_blueprint.get("/investigation-home")
@protected
def investigation_home():
 repo=current_app.extensions["repository"];items=[_normalise_investigation(item) for item in repo.list_investigations_for_user(g.user["id"],10)]
 health=list_sources(repo);degraded=[s for s in health if s["status"]!="Fresh"]
 return _ok({"user":public_user(g.user),"recent_investigations":items,"source_health":health,"degraded_mode":bool(degraded),"degraded_sources":[s["id"] for s in degraded]})

@m3_blueprint.get("/source-control")
@protected
def source_control_centre():
 purpose=request.args.get("purpose")
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
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {};sources=_source_snapshot(payload.get("selected_sources",[]))
 decision=evaluate(g.user,inv["purpose"],sources,"SOURCE_SELECTION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed: audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403)
 repo.replace_investigation_sources(iid,json.dumps(sources),datetime.now(timezone.utc).isoformat());audit(repo,"SOURCE_SELECTION_CHANGED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"source_count":len(sources)});return _ok(_investigation(repo,iid))

@m3_blueprint.post("/investigations/<iid>/sources/preset")
@protected
def apply_preset(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);preset=(request.get_json(silent=True) or {}).get("preset")
 if preset not in PRESETS:raise ApiError("PRESET_NOT_FOUND","Source preset was not found.",404)
 sources=_source_snapshot(PRESETS[preset]);decision=evaluate(g.user,inv["purpose"],sources,"SOURCE_SELECTION",current_app.config["MAX_SEARCH_RESULTS"])
 if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
 repo.replace_investigation_sources(iid,json.dumps(sources),datetime.now(timezone.utc).isoformat());audit(repo,"SOURCE_PRESET_SELECTED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"preset":preset});return _ok(_investigation(repo,iid))

@m3_blueprint.get("/investigations/<iid>/history")
@protected
def history(iid):
 repo=current_app.extensions["repository"];_owned(repo,iid);return _ok(repo.list_investigation_messages(iid))

@m3_blueprint.post("/investigations/<iid>/query/preview")
@protected
def preview(iid):
 repo=current_app.extensions["repository"];inv=_investigation(repo,iid)
 if not inv or inv["user_id"]!=g.user["id"]:raise ApiError("INVESTIGATION_NOT_FOUND","Investigation was not found.",404,False)
 payload=request.get_json(silent=True) or {};plan,engine=_interpret_plan(str(payload.get("query","")),inv["selected_sources"]);decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"SEARCH",plan.result_limit)
 if not decision.allowed:audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 mid=f"SYN-MSG-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo.create_investigation_message({"id":mid,"investigation_id":iid,"original_text":_history_label(plan),"query_plan_json":plan.model_dump_json(),"confirmed":0,"created_at":now,"execution_intent":plan.intent,"request_id":g.request_id});audit(repo,"QUERY_PREVIEW","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"intent":plan.intent,"interpretation_engine":engine})
 states={s["id"]:s["status"] for s in list_sources(repo)};return _ok({"message_id":mid,"original_query":payload["query"],"normalised_interpretation":plan.model_dump(mode="json"),"interpretation_engine":engine,"policy_preview":decision.dict(),"source_states":states,"warnings":["Confirmation required"] if plan.requires_confirmation else []})

@m3_blueprint.post("/investigations/<iid>/query/follow-up")
@protected
def follow_up(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {};parent=payload.get("parent_message_id")
 previous=repo.find_investigation_message(iid,parent)
 if not previous:raise ApiError("CONTEXT_NOT_FOUND","Follow-up context was not found in this investigation.",404)
 plan,engine=_interpret_plan(str(payload.get("query","")),inv["selected_sources"]);old=QueryPlan.model_validate_json(previous["query_plan_json"])
 for field in ("offence","location","date_from","date_to","status"):
  if getattr(plan.filters,field) is None:setattr(plan.filters,field,getattr(old.filters,field))
 plan.selected_sources=old.selected_sources;plan.result_limit=min(plan.result_limit,old.result_limit);plan.protected_tokens=list(dict.fromkeys(old.protected_tokens+plan.protected_tokens))
 mid=f"SYN-MSG-{uuid.uuid4().hex[:12].upper()}";now=datetime.now(timezone.utc).isoformat();repo.create_investigation_message({"id":mid,"investigation_id":iid,"original_text":_history_label(plan),"query_plan_json":plan.model_dump_json(),"confirmed":0,"created_at":now,"parent_message_id":parent});audit(repo,"FOLLOW_UP_PREVIEW","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"parent":parent,"interpretation_engine":engine});return _ok({"message_id":mid,"parent_message_id":parent,"normalised_interpretation":plan.model_dump(mode="json"),"interpretation_engine":engine,"inherited_fields":[f for f in ("offence","location","date_from","date_to","status") if getattr(old.filters,f) is not None and getattr(plan.filters,f)==getattr(old.filters,f)],"requires_confirmation":plan.requires_confirmation})

def _validated_plan(payload):
 try:return QueryPlan.model_validate(payload)
 except ValidationError as error:raise ApiError("INVALID_QUERY_PLAN","Edited query preview is invalid.",400,False) from error

@m3_blueprint.post("/query/validate")
@protected
def validate_plan():return _ok(_validated_plan(request.get_json(silent=True) or {}).model_dump(mode="json"))

@m3_blueprint.post("/investigations/<iid>/query/<mid>/confirm")
@protected
def confirm(iid,mid):
 plan=_validated_plan(request.get_json(silent=True) or {});repo=current_app.extensions["repository"];_owned(repo,iid)
 if not repo.confirm_investigation_message(iid,mid,plan.model_dump_json()):raise ApiError("QUERY_PREVIEW_NOT_FOUND","Query preview was not found.",404,False)
 return _ok({"message_id":mid,"confirmed":True,"plan":plan.model_dump(mode="json")})

@m3_blueprint.post("/investigations/<iid>/search")
@protected
def execute_search(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 plan=_validated_plan(request.get_json(silent=True) or {})
 if plan.intent!="SEARCH":raise ApiError("INTENT_NOT_AVAILABLE",f"{plan.intent} execution is not available until a later milestone.",409,False)
 decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"SEARCH",plan.result_limit)
 if not decision.allowed:audit(repo,"PERMISSION_DENIAL","DENIED",g.user["id"],g.request_id,decision.dict());raise ApiError(decision.denial_code,decision.explanation,403,False)
 results=search_cases(repo,g.user,inv["purpose"],plan);metadata={"investigation_id":iid,"filter_categories":[key for key,value in plan.filters.model_dump().items() if value is not None],"selected_sources":plan.selected_sources,"result_count":len(results)};audit(repo,"FIR_SEARCH_EXECUTED","SUCCESS",g.user["id"],g.request_id,metadata);audit(repo,"SEARCH_EXECUTION","SUCCESS",g.user["id"],g.request_id,metadata)
 states={s["id"]:s["status"] for s in list_sources(repo) if s["id"] in plan.selected_sources};warnings=[f"{sid} is {state}" for sid,state in states.items() if state!="Fresh"]
 return _ok({"results":results,"result_count":len(results),"source_states":states,"policy":decision.dict()},warnings)

@m3_blueprint.post("/investigations/<iid>/answer")
@protected
def grounded_answer(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {}
 plan=_validated_plan(payload.get("plan") or payload)
 question=str(payload.get("question") or "").strip()
 cached=payload.get("results")
 if isinstance(cached,list):
  results=cached
  decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"DISCOVER" if plan.intent=="DISCOVER" else "SEARCH",plan.result_limit)
  if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
 elif plan.intent=="DISCOVER":
  decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"DISCOVER",plan.result_limit)
  if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
  results=discover(repo,g.user,inv["purpose"],plan)
 else:
  if plan.intent!="SEARCH":raise ApiError("INTENT_NOT_AVAILABLE",f"{plan.intent} answer synthesis is not available.",409,False)
  decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"SEARCH",plan.result_limit)
  if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
  results=search_cases(repo,g.user,inv["purpose"],plan)
 answer_payload=llm_answer(question,results,plan,current_app.config) or templated_answer(question or "Investigation query",results,plan)
 audit(repo,"AI_ANSWER","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"engine":answer_payload.get("engine"),"result_count":len(results),"citation_count":len(answer_payload.get("cited_source_ids") or []),"model_used":answer_payload.get("model_used"),"fallback_reason":answer_payload.get("fallback_reason")})
 return _ok(answer_payload)

@m3_blueprint.post("/investigations/<iid>/discover")
@protected
def execute_discover(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);plan=_validated_plan(request.get_json(silent=True) or {})
 if plan.intent!="DISCOVER":raise ApiError("INTENT_REQUIRED","DISCOVER intent is required.",409)
 decision=evaluate(g.user,inv["purpose"],plan.selected_sources,"DISCOVER",plan.result_limit)
 if not decision.allowed:raise ApiError(decision.denial_code,decision.explanation,403)
 results=discover(repo,g.user,inv["purpose"],plan);audit(repo,"DISCOVER_EXECUTION","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"result_count":len(results)});return _ok({"results":results,"result_count":len(results),"candidate_only":True})

@m3_blueprint.get("/investigations/<iid>/analytics/trends")
@protected
def investigation_trends(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=aggregate_crime_trends(repo,g.user,inv["purpose"],inv["selected_sources"])
 audit(repo,"AGGREGATE_TRENDS_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"authorised_case_count":result["summary"]["authorised_case_count"],"selected_sources":inv["selected_sources"]})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/analytics/briefing")
@protected
def investigation_briefing(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=build_shift_briefing(repo,g.user,inv["purpose"],inv["selected_sources"])
 audit(repo,"SHIFT_BRIEFING_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"authorised_case_count":result["summary"]["authorised_case_count"],"selected_sources":inv["selected_sources"]})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/related")
@protected
def related_case_view(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 try: limit=int(request.args.get("limit",10))
 except ValueError: raise ApiError("RELATED_CASE_LIMIT_INVALID","Related case limit must be numeric.",400,False)
 result=related_cases(repo,g.user,inv["purpose"],case_id,inv["selected_sources"],limit)
 audit(repo,"RELATED_CASES_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"base_case_id":case_id,"selected_sources":inv["selected_sources"],"result_count":len(result["related_cases"])})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<left_id>/compare/<right_id>")
@protected
def investigation_case_compare(iid,left_id,right_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=compare_cases(repo,g.user,inv["purpose"],left_id,right_id,inv["selected_sources"])
 audit(repo,"CASE_COMPARE_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"left_case_id":left_id,"right_case_id":right_id})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/priorities")
@protected
def investigation_case_priorities(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=verification_priorities(repo,g.user,inv["purpose"],case_id,inv["selected_sources"])
 audit(repo,"VERIFICATION_PRIORITIES_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"priority_count":len(result["priorities"])})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/brief")
@protected
def investigation_brief(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=grounded_brief(repo,g.user,inv["purpose"],case_id,inv["selected_sources"])
 audit(repo,"GROUNDED_BRIEF_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"selected_sources":inv["selected_sources"]})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/brief.pdf")
@protected
def investigation_brief_pdf(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 brief=grounded_brief(repo,g.user,inv["purpose"],case_id,inv["selected_sources"])
 for exh in brief.get("exhibits") or []:
  if exh.get("thumbnail_masked") or not exh.get("id"):continue
  row=repo.find_case_exhibit(exh["id"])
  if row and row.get("content_blob"):exh["content_blob"]=row["content_blob"]
 audit(repo,"GROUNDED_BRIEF_PDF_GENERATED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"exhibit_count":len(brief.get("exhibits") or [])})
 return send_file(BytesIO(grounded_brief_pdf(brief,inv["title"])),mimetype="application/pdf",as_attachment=True,download_name=f"anvaya-case-dossier-{case_id.lower()}.pdf")

@m3_blueprint.post("/investigations/<iid>/chat/action")
@protected
def investigation_chat_action(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {}
 text=str(payload.get("query") or payload.get("text") or "")
 context=payload.get("context") if isinstance(payload.get("context"),dict) else {}
 result=resolve_chat_action(text,context)
 audit(repo,"CHAT_ACTION_RESOLVED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"kind":result.get("kind"),"action":result.get("action"),"case_ref":result.get("case_ref")})
 return _ok(result)

@m3_blueprint.post("/investigations/<iid>/conversation.pdf")
@protected
def investigation_conversation_pdf(iid):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {}
 turns=payload.get("turns") if isinstance(payload.get("turns"),list) else []
 safe_turns=[]
 for turn in turns[:200]:
  if not isinstance(turn,dict):continue
  safe_turns.append({"role":str(turn.get("role") or "unknown")[:40],"kind":str(turn.get("kind") or "text")[:40],"text":str(turn.get("text") or "")[:4000],"created_at":str(turn.get("created_at") or "")[:64]})
 audit(repo,"CONVERSATION_PDF_GENERATED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"turn_count":len(safe_turns)})
 return send_file(BytesIO(conversation_pdf(safe_turns,inv["title"],iid)),mimetype="application/pdf",as_attachment=True,download_name=f"anvaya-conversation-{iid.lower()}.pdf")

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/network-clusters")
@protected
def investigation_network_clusters(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=candidate_network_clusters(repo,g.user,inv["purpose"],case_id,inv["selected_sources"])
 audit(repo,"NETWORK_CLUSTERS_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"cluster_count":len(result.get("clusters") or [])})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/graph")
@protected
def fir_graph_view(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=fir_relationship_graph(repo,g.user,inv["purpose"],case_id,inv["selected_sources"])
 graph_data=result["graph"];audit(repo,"FIR_GRAPH_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"base_case_id":case_id,"selected_sources":inv["selected_sources"],"node_count":graph_data["node_count"],"edge_count":graph_data["edge_count"]})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/graph/path")
@protected
def fir_graph_path_view(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=fir_relationship_path(repo,g.user,inv["purpose"],case_id,request.args.get("to", ""),inv["selected_sources"],request.args.get("max_hops",3))
 audit(repo,"FIR_RELATIONSHIP_PATH_VIEWED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"base_case_id":case_id,"hop_count":result["hop_count"],"selected_sources":inv["selected_sources"]})
 return _ok(result)

@m3_blueprint.get("/investigations/<iid>/cases/<case_id>/assurance")
@protected
def fir_assurance_view(iid,case_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid)
 result=list_case_assurance(repo,g.user,inv["purpose"],case_id,inv["selected_sources"],request.args.get("status"))
 audit(repo,"FIR_ASSURANCE_EXECUTED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"summary":result["summary"]})
 return _ok(result)

@m3_blueprint.patch("/investigations/<iid>/cases/<case_id>/assurance/<finding_id>")
@protected
def fir_assurance_update(iid,case_id,finding_id):
 repo=current_app.extensions["repository"];inv=_owned(repo,iid);payload=request.get_json(silent=True) or {}
 status=str(payload.get("status", ""));note=str(payload.get("note", ""))[:500]
 if status not in {"ACKNOWLEDGED", "RESOLVED"}: raise ApiError("ASSURANCE_STATUS_INVALID", "Assurance status is invalid.", 400, False)
 row=set_assurance_status(repo,g.user,inv["purpose"],case_id,finding_id,status,note)
 audit(repo,"FIR_ASSURANCE_FINDING_ACKNOWLEDGED" if status=="ACKNOWLEDGED" else "FIR_ASSURANCE_FINDING_RESOLVED","SUCCESS",g.user["id"],g.request_id,{"investigation_id":iid,"case_id":case_id,"finding_id":finding_id,"new_status":status})
 return _ok({"id":row["id"],"status":row["status"]})

@m3_blueprint.get("/cases/<case_id>/360")
@protected
def case_review(case_id):
 purpose=request.args.get("purpose");result=case_360(current_app.extensions["repository"],g.user,purpose,case_id);audit(current_app.extensions["repository"],"CASE_360_OPENED","SUCCESS",g.user["id"],g.request_id,{"case_id":case_id,"masking_level":result["overview"]["masking"]["level"]});return _ok(result)

@m3_blueprint.get("/source-passports/<source_record_id>")
@protected
def source_passport(source_record_id):
 purpose=request.args.get("purpose");result=passport(current_app.extensions["repository"],g.user,purpose,source_record_id);audit(current_app.extensions["repository"],"SOURCE_PASSPORT_VIEWED","SUCCESS",g.user["id"],g.request_id,{"source_record_id":source_record_id});return _ok(result)

@m3_blueprint.get("/relationships/path")
@protected
def path():
 result=relationship_path(current_app.extensions["repository"],g.user,request.args.get("purpose"),request.args.get("from",""),request.args.get("to",""),request.args.get("max_hops",3));audit(current_app.extensions["repository"],"RELATIONSHIP_PATH_REQUESTED","SUCCESS",g.user["id"],g.request_id,{"path_length":len(result["path"])});return _ok(result)

@m3_blueprint.get("/m5/case-dna/<left>/<right>")
@protected
def m5_dna(left,right):
 result=dna(current_app.extensions["repository"],g.user,request.args.get("purpose"),left,right);audit(current_app.extensions["repository"],"CASE_DNA_COMPARISON","SUCCESS",g.user["id"],g.request_id,{"score":result["score"]});return _ok(result)
@m3_blueprint.get("/m5/graph/<case_id>")
@protected
def m5_graph(case_id):
 result=graph(current_app.extensions["repository"],g.user,request.args.get("purpose"),case_id,request.args.get("hops",3));audit(current_app.extensions["repository"],"EVIDENCE_GRAPH_OPENED","SUCCESS",g.user["id"],g.request_id,{"nodes":len(result["nodes"])});return _ok(result)
@m3_blueprint.get("/m5/assurance/<case_id>")
@protected
def m5_assurance(case_id):return _ok(list_case_assurance(current_app.extensions["repository"],g.user,request.args.get("purpose"),case_id,("CCTNS_REPLICA",)))
@m3_blueprint.get("/m5/verify/<left>/<right>")
@protected
def m5_verify(left,right):
 result=verify(current_app.extensions["repository"],g.user,request.args.get("purpose"),left,right);audit(current_app.extensions["repository"],"VERIFY_EXECUTED","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
@m3_blueprint.post("/m5/challenge/<case_id>")
@protected
def m5_challenge(case_id):
 result=challenge(current_app.extensions["repository"],g.user,request.args.get("purpose"),case_id,str((request.get_json(silent=True) or {}).get("hypothesis","")));audit(current_app.extensions["repository"],"HYPOTHESIS_CHALLENGE","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
@m3_blueprint.get("/m5/actions/<case_id>")
@protected
def m5_actions(case_id):
 result=actions(current_app.extensions["repository"],g.user,request.args.get("purpose"),case_id);audit(current_app.extensions["repository"],"ACTION_IMPACT_PREVIEW","SUCCESS",g.user["id"],g.request_id,{});return _ok(result)
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
 v=repo.list_report_versions(rid);history=repo.list_report_review_history(rid);audit(repo,'REPORT_VIEWED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok({'report':r,'versions':v,'review_history':history,'allowed_actions':['review'] if g.user['role']=='SUPERVISOR' else ['update','submit']})
@m3_blueprint.get('/reports/<rid>/versions/<int:number>')
@protected
def reports_version(rid,number):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 row=repo.find_report_version(rid,number)
 if not row:raise ApiError('VERSION_NOT_FOUND','Report version was not found.',404)
 audit(repo,'REPORT_VERSION_VIEWED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid,'version_number':number});return _ok({key:row[key] for key in ('id','version_number','status','sections_json','notes','created_by','created_at','immutable')})
@m3_blueprint.get('/reviewers')
@protected
def reviewers():
 return _ok(current_app.extensions['repository'].list_eligible_supervisors())
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
def reports_new_version(rid):
 result=new_version(current_app.extensions['repository'],g.user,rid);audit(current_app.extensions['repository'],'REPORT_VERSION_CREATED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid,'version_id':result['version_id']});return _ok(result)
@m3_blueprint.get('/reports/<rid>/preview')
@protected
def reports_preview(rid):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 row=repo.find_current_report_version(rid)
 if not row:raise ApiError('VERSION_NOT_FOUND','Report version was not found.',404)
 audit(repo,'REPORT_PREVIEW_GENERATED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok({'report_id':rid,'html':row['html'],'export':'browser-print-to-PDF'})
@m3_blueprint.get('/reports/<rid>/preview-metadata')
@protected
def reports_preview_metadata(rid):
 repo=current_app.extensions['repository'];r=_report(repo,rid)
 if not allowed(repo,g.user,r):raise ApiError('REPORT_DENIED','Report access is denied.',403)
 v=repo.find_current_report_version(rid);reviewer=repo.find_user_by_id(r['assigned_reviewer_id']) if r['assigned_reviewer_id'] else None
 if not v:raise ApiError('VERSION_NOT_FOUND','Report version was not found.',404)
 return _ok({'report_id':rid,'title':r['title'],'version_number':v['version_number'],'status':r['status'],'generated_by':v['created_by'],'reviewed_by':reviewer['username'] if reviewer else None,'generated_timestamp':v['created_at'],'selected_sections':json.loads(v['sections_json']),'masking_notices':['Masking remains policy-filtered.'],'jurisdiction_notices':['Jurisdiction is re-evaluated at access time.'],'stale_source_warnings':[],'unavailable_source_warnings':['Court and Prosecution are unavailable P1 metadata.'],'missing_provenance_warnings':['Missing provenance is disclosed where seeded.'],'provenance_summary':{'count':0,'safe':'Source-backed references are retained in the report.'},'filename':f"anvaya-{rid.lower()}-v{v['version_number']}.html",'native_pdf_available':False,'browser_print_to_pdf_available':True,'allowed_actions':['review'] if g.user['role']=='SUPERVISOR' else ['preview','submit']})
@m3_blueprint.post('/reports/<rid>/review')
@protected
def reports_review(rid):
 p=request.get_json(silent=True) or {};result=review_report(current_app.extensions['repository'],g.user,rid,str(p.get('decision','')),str(p.get('note','')));repo=current_app.extensions['repository'];audit(repo,'REPORT_REVIEWED','SUCCESS',g.user['id'],g.request_id,{'report_id':rid,'decision':result['status']});event={'APPROVED':'REPORT_APPROVED','CHANGES_REQUESTED':'REPORT_RETURNED','REJECTED':'REPORT_REJECTED'}[result['status']];audit(repo,event,'SUCCESS',g.user['id'],g.request_id,{'report_id':rid});return _ok(result)
@m3_blueprint.get('/system-health')
@protected
def system_health():
 repo=current_app.extensions['repository'];sources=list_sources(repo);return _ok({'backend':'ok','database':repo.health_check(),'migration_version':repo.schema_version(),'frontend_build':'M6 local build','sources':sources,'optional_ai':'disabled','report_export':'browser-print-to-PDF','degraded_mode':any(s['status']!='Fresh' for s in sources),'degraded_reasons':[f"{source['name']} is {source['status']}" for source in sources if source['status']!='Fresh'],'warnings':['Synthetic source limitations remain visible in all results.'],'platform_capabilities':current_app.extensions['platform_capabilities'].safe_dict()})
@m3_blueprint.get('/audit-events')
@protected
def audit_events():
 repo=current_app.extensions['repository'];rows,limit,offset=list_events(repo,g.user,request.args)
 audit(repo,'AUDIT_DASHBOARD_VIEWED','SUCCESS',g.user['id'],g.request_id,{'count':len(rows)});return _ok({'events':rows,'limit':limit,'offset':offset})
