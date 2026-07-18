from backend.anvaya.services.generator import generate
P="ANVAYA-DEMO-ONLY-2026"
def login(c):return c.post('/api/auth/login',json={'username':'investigator.demo','password':P})
def test_m5_dna_graph_assurance_verify_challenge_actions(client,app):
 generate(app.extensions['repository'],app.config,'test');login(client)
 for url in ['/api/m5/case-dna/SYN-CASE-0001/SYN-CASE-0002','/api/m5/graph/SYN-CASE-0001','/api/m5/assurance/SYN-CASE-0001','/api/m5/verify/SYN-CASE-0001/SYN-CASE-0002','/api/m5/actions/SYN-CASE-0001']:
  assert client.get(url).status_code==200
 dna=client.get('/api/m5/case-dna/SYN-CASE-0001/SYN-CASE-0002').json['data'];assert dna['score']<=100 and any(x['factor']=='hard_device' for x in dna['factors'])
 assert client.post('/api/m5/challenge/SYN-CASE-0001',json={'hypothesis':'These cases may connect'}).status_code==200
 assert client.post('/api/m5/challenge/SYN-CASE-0001',json={'hypothesis':'select * from cases'}).status_code==400
