from backend.anvaya import create_app
from backend.anvaya.api.m3 import _login_rate
from backend.anvaya.services.generator import generate
def login(c,u='investigator.demo'):return c.post('/api/auth/login',json={'username':u,'password':c.application.config['DEMO_PASSWORD']})
def report(c):
 inv=c.post('/api/investigations',json={'title':'M6 report test','purpose':'Active Case Investigation','selected_sources':['CCTNS_REPLICA']}).json['data'];return c.post('/api/reports',json={'title':'Report','investigation_id':inv['id'],'sections':['Cover','Disclaimer'],'notes':'Synthetic report note.'}).json['data']
def test_m6_preview_list_assignment_review_and_audit_filters(client,app):
 generate(app.extensions['repository'],app.config,'test');login(client);r=report(client);rid=r['report_id']
 assert client.get('/api/reports').status_code==200
 assert client.get(f'/api/reports/{rid}/preview-metadata').json['data']['native_pdf_available'] is False
 assert client.post(f'/api/reports/{rid}/assign',json={'reviewer':'supervisor.demo'}).status_code==200
 assert client.post(f'/api/reports/{rid}/submit').status_code==200
 client.post('/api/auth/logout');login(client,'supervisor.demo');assert client.get('/api/reports').json['data']['reports']
 assert client.post(f'/api/reports/{rid}/review',json={'decision':'REJECTED','note':''}).status_code==400
 assert client.post(f'/api/reports/{rid}/review',json={'decision':'CHANGES_REQUESTED','note':'Need source check'}).status_code==200
 assert client.get('/api/audit-events?actor_role=INVESTIGATOR&limit=999').json['data']['limit']==50
 assert client.get('/api/audit-events?investigation=bad').status_code==400
 assert client.get('/api/audit-events?report=bad').status_code==400
 assert client.get('/api/audit-events?actor_role=BAD').status_code==400


def test_m6_report_scope_versions_history_and_safe_preview(client,app):
 generate(app.extensions['repository'],app.config,'test');login(client);created=client.post('/api/investigations',json={'title':'M6 safe preview','purpose':'Active Case Investigation','selected_sources':['CCTNS_REPLICA']}).json['data'];created=client.post('/api/reports',json={'title':'Report','investigation_id':created['id'],'sections':['Cover','Reviewer Notes','Disclaimer'],'notes':'Synthetic report note.'}).json['data'];rid=created['report_id']
 assert '<script>' not in created['html'] and 'Synthetic report note.' in created['html']
 assert client.post(f'/api/reports/{rid}/assign',json={'reviewer':'analyst.demo'}).status_code==400
 assert client.post(f'/api/reports/{rid}/assign',json={'reviewer':'supervisor.demo'}).status_code==200
 assert client.post(f'/api/reports/{rid}/submit').status_code==200
 version=client.get(f'/api/reports/{rid}/versions/1');assert version.status_code==200 and version.json['data']['immutable']==1
 client.post('/api/auth/logout');login(client,'analyst.demo');assert client.get(f'/api/reports/{rid}').status_code==403
 client.post('/api/auth/logout');login(client,'supervisor.demo');assert client.post(f'/api/reports/{rid}/review',json={'decision':'REJECTED','note':'required'}).status_code==200
 assert client.get(f'/api/reports/{rid}').json['data']['review_history'][0]['decision']=='REJECTED'


def test_m6_audit_filter_scope_and_metadata(client,app):
 generate(app.extensions['repository'],app.config,'test');login(client);created=report(client);rid=created['report_id']
 response=client.get('/api/audit-events',query_string={'event_type':'REPORT_DRAFT_CREATED','report':rid,'actor_role':'INVESTIGATOR','limit':999})
 assert response.status_code==200 and response.json['data']['limit']==50
 assert all('password' not in str(event).lower() and 'token' not in str(event).lower() for event in response.json['data']['events'])
 assert client.get('/api/audit-events?start=not-a-date').status_code==400
 assert client.get('/api/audit-events?start=2027-01-01T00:00:00Z&end=2026-01-01T00:00:00Z').status_code==400
 assert client.delete('/api/audit-events').status_code==405


def test_m6_production_configuration_cookie_rate_and_request_limits():
 config={'DATABASE_URL':'sqlite:///:memory:','SESSION_SECRET':'x'*32,'ALLOWED_ORIGINS':'https://anvaya.example.test','LOGIN_RATE_LIMIT_PER_MINUTE':1,'MAX_CONTENT_LENGTH':128,'MAX_UPLOAD_BYTES':64}
 app=create_app('production',config);c=app.test_client();_login_rate.clear()
 first=c.post('/api/auth/login',json={'username':'investigator.demo','password':app.config['DEMO_PASSWORD']});assert first.status_code==200 and 'Secure' in first.headers['Set-Cookie'] and 'SameSite=Strict' in first.headers['Set-Cookie']
 second=c.post('/api/auth/login',json={'username':'investigator.demo','password':app.config['DEMO_PASSWORD']});assert second.status_code==429 and second.json['code']=='LOGIN_RATE_LIMITED'
 _login_rate.clear();oversized=c.post('/api/auth/login',data='x'*256,content_type='application/json');assert oversized.status_code==413 and 'Traceback' not in oversized.get_data(as_text=True)
 app.extensions['repository'].close()
