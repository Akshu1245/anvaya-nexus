from __future__ import annotations
import html,json,uuid
from datetime import datetime,timezone
from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.investigation import case_360
SECTIONS=("Cover","Investigation Summary","Purpose and Scope","Selected Sources","Search Criteria","Retrieved Cases","Candidate Relationships","Case DNA Comparisons","Evidence Graph Summary","Record Assurance Findings","Hypothesis Challenge","Action Impact Preview","VERIFY Findings","Source Limitations","Jurisdiction and Masking Notes","Provenance Appendix","Audit Reference","Reviewer Notes","Disclaimer")
def _now():return datetime.now(timezone.utc).isoformat()
def _report(repo,id):
 row=repo.connection.execute("SELECT * FROM reports WHERE id=?",(id,)).fetchone()
 if not row:raise ApiError("REPORT_NOT_FOUND","Report was not found.",404)
 return dict(row)
def render(repo,report,sections,notes,user):
 inv=repo.connection.execute("SELECT * FROM investigations WHERE id=?",(report["investigation_id"],)).fetchone(); source=[dict(x) for x in repo.connection.execute("SELECT * FROM source_systems")];safe=html.escape(notes)
 blocks=[]
 for name in sections:
  if name=="Cover":body=f"<p>Report ID: {report['id']} · Generated: {_now()}</p>"
  elif name=="Investigation Summary":body=f"<p>{html.escape(inv['title'])} · {html.escape(inv['purpose'])}</p>"
  elif name=="Selected Sources":body="<ul>"+"".join(f"<li>{html.escape(x['name'])}: {x['status']}</li>" for x in source)+"</ul>"
  elif name=="Reviewer Notes":body=f"<p class='note'>{safe}</p>"
  elif name=="Disclaimer":body="<p>SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE. Candidate-support only; no identity, guilt, risk, or operational conclusion.</p>"
  elif name=="Jurisdiction and Masking Notes":body="<p>Current policy and masking are re-evaluated before generation. Source limitations and unavailable data remain visible.</p>"
  else:body="<p>Source-backed section available through the authorised investigation record. No invented narrative is generated.</p>"
  blocks.append(f"<section><h2>{html.escape(name)}</h2>{body}</section>")
 return "<!doctype html><html><head><meta charset='utf-8'><title>ANVAYA report</title><style>body{font-family:system-ui;margin:2rem;color:#111}section{break-inside:avoid;border-bottom:1px solid #ddd;padding:1rem 0}.note{white-space:pre-wrap}@media print{section{page-break-inside:avoid}}</style></head><body><header><strong>SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE</strong></header>"+"".join(blocks)+"</body></html>"
def create(repo,user,payload):
 iid=payload.get('investigation_id');inv=repo.connection.execute("SELECT * FROM investigations WHERE id=? AND user_id=?",(iid,user['id'])).fetchone()
 if not inv:raise ApiError("INVESTIGATION_NOT_FOUND","Investigation was not found.",404)
 rid='SYN-RPT-'+uuid.uuid4().hex[:12].upper();now=_now();sections=[x for x in payload.get('sections',SECTIONS) if x in SECTIONS];report={'id':rid,'investigation_id':iid,'owner_user_id':user['id'],'title':str(payload.get('title','ANVAYA report')),'status':'DRAFT','current_version':1};doc=render(repo,report,sections,str(payload.get('notes','')),user);vid=rid+'-V1';repo.connection.execute("INSERT INTO reports (id,investigation_id,owner_user_id,title,status,current_version,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",(rid,iid,user['id'],report['title'],'DRAFT',1,now,now));repo.connection.execute("INSERT INTO report_versions VALUES (?,?,?,?,?,?,?,?,?,?)",(vid,rid,1,'DRAFT',json.dumps(sections),str(payload.get('notes','')),doc,user['id'],now,0));repo.connection.commit();return {'report_id':rid,'version_id':vid,'html':doc,'status':'DRAFT'}
def submit(repo,user,rid):
 report=_report(repo,rid)
 if report['owner_user_id']!=user['id']:raise ApiError('REPORT_DENIED','Report access is denied.',403)
 if report['status'] not in {'DRAFT','CHANGES_REQUESTED'}:raise ApiError('INVALID_REPORT_TRANSITION','This report cannot be submitted from its current status.',409)
 repo.connection.execute("UPDATE reports SET status='IN_REVIEW',updated_at=? WHERE id=?",(_now(),rid));repo.connection.execute("UPDATE report_versions SET status='IN_REVIEW',immutable=1 WHERE report_id=? AND version_number=?",(rid,report['current_version']));repo.connection.commit();return {'report_id':rid,'status':'IN_REVIEW'}
def update(repo,user,rid,payload):
 report=_report(repo,rid)
 if report['owner_user_id']!=user['id'] or report['status']!='DRAFT':raise ApiError('REPORT_IMMUTABLE','Only an owned draft can be edited.',409)
 sections=[x for x in payload.get('sections',SECTIONS) if x in SECTIONS];notes=str(payload.get('notes',''));doc=render(repo,report,sections,notes,user);repo.connection.execute("UPDATE report_versions SET sections_json=?,notes=?,html=? WHERE report_id=? AND version_number=?",(json.dumps(sections),notes,doc,rid,report['current_version']));repo.connection.execute("UPDATE reports SET title=?,updated_at=? WHERE id=?",(str(payload.get('title',report['title'])),_now(),rid));repo.connection.commit();return {'report_id':rid,'status':'DRAFT','html':doc}
def new_version(repo,user,rid):
 report=_report(repo,rid)
 if report['owner_user_id']!=user['id'] or report['status']!='CHANGES_REQUESTED':raise ApiError('VERSION_DENIED','A new version is available only after requested changes.',409)
 old=repo.connection.execute("SELECT * FROM report_versions WHERE report_id=? AND version_number=?",(rid,report['current_version'])).fetchone();n=report['current_version']+1;vid=f'{rid}-V{n}';repo.connection.execute("INSERT INTO report_versions VALUES (?,?,?,?,?,?,?,?,?,?)",(vid,rid,n,'DRAFT',old['sections_json'],old['notes'],old['html'],user['id'],_now(),0));repo.connection.execute("UPDATE reports SET current_version=?,status='DRAFT',updated_at=? WHERE id=?",(n,_now(),rid));repo.connection.commit();return {'report_id':rid,'version_id':vid,'status':'DRAFT'}
def review(repo,user,rid,decision,note):
 report=_report(repo,rid)
 if user['role']!='SUPERVISOR' or report['owner_user_id']==user['id'] or report['assigned_reviewer_id']!=user['id'] or report['status']!='IN_REVIEW':raise ApiError('REVIEW_DENIED','Review access is denied.',403)
 if decision not in {'APPROVED','REJECTED','CHANGES_REQUESTED'}:raise ApiError('INVALID_DECISION','Invalid review decision.',400)
 if decision in {'REJECTED','CHANGES_REQUESTED'} and not note.strip():raise ApiError('REVIEW_NOTE_REQUIRED','A review comment is required.',400)
 v=repo.connection.execute("SELECT id FROM report_versions WHERE report_id=? AND version_number=?",(rid,report['current_version'])).fetchone()[0];repo.connection.execute("INSERT INTO report_reviews VALUES (?,?,?,?,?,?)",('SYN-REV-'+uuid.uuid4().hex[:12].upper(),v,user['id'],decision,note,_now()));repo.connection.execute("UPDATE reports SET status=?,updated_at=? WHERE id=?",(decision,_now(),rid));repo.connection.commit();return {'report_id':rid,'status':decision}
def allowed(repo,user,report):return report['owner_user_id']==user['id'] or (user['role']=='SUPERVISOR' and report['assigned_reviewer_id']==user['id'])
def listing(repo,user,limit=25,offset=0):
 sql="SELECT r.*,u.username AS owner_name,s.username AS reviewer_name FROM reports r JOIN users u ON u.id=r.owner_user_id LEFT JOIN users s ON s.id=r.assigned_reviewer_id";args=[]
 if user['role']=='SUPERVISOR':sql+=' WHERE r.assigned_reviewer_id=?';args=[user['id']]
 else:sql+=' WHERE r.owner_user_id=?';args=[user['id']]
 rows=[dict(x) for x in repo.connection.execute(sql+' ORDER BY r.updated_at DESC LIMIT ? OFFSET ?',(*args,limit,offset))];return rows
def assign(repo,user,rid,reviewer):
 r=_report(repo,rid)
 if r['owner_user_id']!=user['id'] or r['status'] not in {'DRAFT','IN_REVIEW','CHANGES_REQUESTED'}:raise ApiError('ASSIGNMENT_DENIED','Reviewer assignment is denied.',403)
 candidate=repo.connection.execute("SELECT * FROM users WHERE username=? AND role='SUPERVISOR' AND active=1",(reviewer,)).fetchone()
 if not candidate:raise ApiError('INVALID_REVIEWER','Reviewer must be an eligible synthetic Supervisor.',400)
 repo.connection.execute("UPDATE reports SET assigned_reviewer_id=?,updated_at=? WHERE id=?",(candidate['id'],_now(),rid));repo.connection.commit();return {'report_id':rid,'reviewer':candidate['username']}
