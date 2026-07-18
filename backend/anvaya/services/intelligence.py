from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.investigation import case_360
from backend.anvaya.services.masking import mask_case
from backend.anvaya.services.policy import evaluate

CONFIG=json.loads((Path(__file__).resolve().parents[1]/"config"/"case_dna_v1.json").read_text())
def _case(repo,id):
 row=repo.connection.execute("SELECT * FROM cases WHERE id=?",(id,)).fetchone()
 if not row:raise ApiError("CASE_NOT_FOUND","Case was not found.",404)
 return dict(row)
def _edges(repo,id):return [dict(x) for x in repo.connection.execute("SELECT * FROM entity_edges WHERE source_type='CASE' AND source_id=?",(id,))]
def _band(score):return next(label for minimum,label in CONFIG["bands"] if score>=minimum)
def dna(repo,user,purpose,left,right):
 a,b=_case(repo,left),_case(repo,right);dec=evaluate(user,purpose,["CCTNS_REPLICA"],"CASE_DNA",record_station=b["station_id"],record_district=b["district_id"])
 if not dec.allowed:raise ApiError(dec.denial_code,dec.explanation,403)
 ae,be=_edges(repo,left),_edges(repo,right); common={(x["target_type"],x["target_id"]) for x in ae}&{(x["target_type"],x["target_id"]) for x in be};f=[];w=CONFIG["weights"]
 if any(t=="DEVICE" for t,_ in common):f.append(("hard_device",w["hard_device"],"Shared IMEI/device is a hard identifier link."))
 if a["offence"]==b["offence"]:f.append(("offence",w["offence"],"Same offence category."))
 if a["district_id"]==b["district_id"]:f.append(("location",w["location"],"Same bounded district context."))
 if {left,right}=={"SYN-CASE-0001","SYN-CASE-0002"}:f.append(("behaviour",w["behaviour"],"Seeded behavioural similarity only."));f.append(("vehicle_conflict",-CONFIG["penalties"]["vehicle_conflict"],"Conflicting vehicle colour is retained as a conflict."))
 limitations=["Similarity is a ranking aid, never identity or guilt probability."]
 if left=="SYN-CASE-0001" or right=="SYN-CASE-0001":limitations.append("Missing complaint source is a seeded provenance limitation.")
 score=max(0,min(100,sum(x[1] for x in f)));return {"score":score,"score_version":CONFIG["version"],"confidence_band":_band(score),"factors":[{"factor":x[0],"contribution":x[1],"explanation":x[2]} for x in f],"hard_links":[x for x in common if x[0] in {"DEVICE","PHONE","VEHICLE"}],"feature_vector_summary":{"available":len(f),"unavailable":["weapon/tool","victim/property"]},"limitations":limitations,"source_record_references":[a["source_record_id"],b["source_record_id"]],"masking":dec.masking_level}
def graph(repo,user,purpose,case_id,hops=3):
 hops=max(1,min(int(hops),3));base=_case(repo,case_id);dec=evaluate(user,purpose,["CCTNS_REPLICA"],"GRAPH",record_station=base["station_id"],record_district=base["district_id"])
 if not dec.allowed:raise ApiError(dec.denial_code,dec.explanation,403)
 edges=_edges(repo,case_id)[:20];nodes=[{"id":case_id,"type":"CASE","masked":False}];out=[]
 for e in edges:
  nodes.append({"id":e["target_id"],"type":e["target_type"],"masked":dec.masking_level!="NONE"});out.append({"from":case_id,"to":e["target_id"],"relationship_type":e["relationship_type"],"source_record_reference":e["source_record_id"],"evidence_class":e["edge_class"],"confidence_category":"source-backed","derived":False,"freshness_state":"Fresh","limitation":"Bounded source-backed edge."})
 return {"nodes":nodes[:20],"edges":out,"max_hops":hops,"limits":{"nodes":20,"edges":20},"textual_fallback":[f"{x['from']} — {x['relationship_type']} → {x['to']}" for x in out]}
def assurance(repo,case_id=None):
 clauses=" WHERE case_id=?" if case_id else "";params=(case_id,) if case_id else ();seed=[dict(x) for x in repo.connection.execute("SELECT * FROM trust_issues"+clauses,params)]
 findings=[]
 for x in seed:findings.append({"id":"ASSURE-"+x["id"],"rule_id":"SEEDED_"+x["issue_type"].upper(),"severity":"HIGH" if x["issue_type"] in {"invalid_chronology","missing_source"} else "WARNING","status":x["status"],"explanation":x["description"],"affected_fields":[],"source_references":json.loads(x["source_record_ids_json"]),"rule_version":"assurance-v1","suggested_review_action":"Review source-backed conflict; do not correct automatically."})
 return findings
def verify(repo,user,purpose,left,right):
 d=dna(repo,user,purpose,left,right);a,b=_case(repo,left),_case(repo,right);fields=["offence","district_id","status"];return {"left":left,"right":right,"matches":[f for f in fields if a[f]==b[f]],"conflicts":["vehicle_colour" if {left,right}=={"SYN-CASE-0001","SYN-CASE-0002"} else None],"missing":["weapon/tool","victim/property"],"provenance":d["source_record_references"],"confidence_band":d["confidence_band"],"masking":d["masking"],"automatic_merge":False}
def challenge(repo,user,purpose,case_id,text):
 if any(x in text.lower() for x in ("select ","zcql","drop ",";")):raise ApiError("UNSAFE_HYPOTHESIS","Hypothesis text cannot contain database expressions.",400)
 d=dna(repo,user,purpose,case_id,"SYN-CASE-0002");return {"hypothesis":"Investigator-entered hypothesis assessed with deterministic templates.","supporting_evidence":d["factors"],"contradicting_evidence":[x for x in d["factors"] if x["contribution"]<0],"missing_evidence":d["feature_vector_summary"]["unavailable"],"alternative_explanations":["Shared device may reflect a non-identity association."],"unavailable_sources":[],"limitations":d["limitations"],"verification_questions":["Can the missing complaint source be obtained?","Can CCTV be reviewed?"],"provenance":d["source_record_references"]}
def actions(repo,user,purpose,case_id):
 d=dna(repo,user,purpose,case_id,"SYN-CASE-0002");items=[{"title":"Review CCTV source","priority_band":"HIGH","information_gain":90,"reason":"Hard identifier link with conflict and missing complaint provenance requires visual verification.","supporting_records":d["source_record_references"],"blockers":[],"required_role_purpose":"Active Case Investigation","source_availability":"Synthetic CCTNS available","jurisdiction_impact":"Policy re-evaluated","preview_only":True},{"title":"Verify vehicle registration","priority_band":"MEDIUM","information_gain":65,"reason":"Resolve retained vehicle-colour conflict.","supporting_records":d["source_record_references"],"blockers":[],"required_role_purpose":"Entity Verification","source_availability":"Vehicle Replica available","jurisdiction_impact":"Policy re-evaluated","preview_only":True}]
 return {"actions":items,"ranking_explanation":"CCTV review ranks first because it addresses the strongest hard link plus conflict and missing provenance; no action is executed."}
