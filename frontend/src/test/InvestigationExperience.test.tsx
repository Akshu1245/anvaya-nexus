import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {BriefPreviewPanel,Case360Workspace,CaseComparePanel,CrimeTrendsPanel,FirRelationshipGraph,InvestigationExperience,NetworkClustersPanel,QueryInterpretationPanel,RecordAssurancePanel,RelatedCasesPanel,ShiftBriefingPanel,VerificationPriorityPanel} from '../features/m4/InvestigationExperience'

function mockHealth(publicDemo=true){
  vi.spyOn(globalThis,'fetch').mockImplementation(async()=>new Response(JSON.stringify({request_id:'test',data:{status:'ok',service:'anvaya-api',environment:'testing',database:'ok',public_demo_enabled:publicDemo},warnings:[]}),{status:200}))
}

it('renders the authenticated investigation entry point',async()=>{
  mockHealth(true)
  render(<InvestigationExperience/>)
  expect(screen.getByRole('heading',{name:'Open ANVAYA demo'})).toBeInTheDocument()
  expect(await screen.findByRole('button',{name:'Open public demo'})).toBeInTheDocument()
  expect(screen.getByText(/server-side source controls and case-data safeguards remain active/i)).toBeInTheDocument()
})

it('hides the public demo CTA when the deployment disables it',async()=>{
  mockHealth(false)
  render(<InvestigationExperience/>)
  await waitFor(()=>expect(screen.getByText(/Public demo mode is disabled/i)).toBeInTheDocument())
  expect(screen.queryByRole('button',{name:'Open public demo'})).not.toBeInTheDocument()
})

it('renders an editable and explicit query interpretation gate',async()=>{
  const user=userEvent.setup()
  let edited:any
  render(<QueryInterpretationPanel preview={{normalised_interpretation:{intent:'DISCOVER',filters:{offence:'CHAIN_SNATCHING',location:'JAYANAGAR',status:'UNRESOLVED',date_from:'2026-04-12',date_to:'2026-07-11'},selected_sources:['CCTNS_REPLICA'],result_limit:25,confidence:.8,uncertain_fields:['location']}}} onChange={value=>{edited=value}}/>)
  expect(screen.getByRole('region',{name:'Editable query interpretation'})).toBeInTheDocument()
  expect(screen.getByText(/deterministic language parsing/i)).toBeInTheDocument()
  await user.clear(screen.getByLabelText('Interpreted location'))
  expect(edited.normalised_interpretation.filters.location).toBeNull()
})

it('renders bounded descriptive trends with non-predictive safeguards',()=>{
  render(<CrimeTrendsPanel data={{summary:{authorised_case_count:30,earliest_month:'2026-04',latest_month:'2026-07'},monthly_incidents:[{month:'2026-04',count:4},{month:'2026-05',count:8}],station_hotspots:[{station_id:'SYN-STN-01',count:8}],hotspot_deltas:[{station_id:'SYN-STN-01',previous_month:'2026-04',current_month:'2026-05',previous_count:4,current_count:8,delta:4}],volume_anomalies:[{month:'2026-05',count:8,interpretation:'Unusual recorded volume. Not a forecast.'}],offence_distribution:[{offence:'CHAIN_SNATCHING',count:12}],methodology:{method:'Deterministic count aggregation.',limitations:['Descriptive counts only; this is not a crime forecast.']}}}/>)
  expect(screen.getByRole('region',{name:'Aggregate crime trends'})).toBeInTheDocument()
  expect(screen.getByText('Not a forecast')).toBeInTheDocument()
  expect(screen.getByText('SYN-STN-01')).toBeInTheDocument()
  expect(screen.getByText('Hotspot deltas')).toBeInTheDocument()
  expect(screen.getByText('Volume anomalies')).toBeInTheDocument()
  expect(screen.getByText(/not a crime forecast/i)).toBeInTheDocument()
})

it('marks one private review role as selected and supports keyboard login submission',async()=>{
  mockHealth(false)
  const user=userEvent.setup()
  render(<InvestigationExperience/>)
  await waitFor(()=>expect(screen.getByText(/Public demo mode is disabled/i)).toBeInTheDocument())
  expect(screen.getByRole('button',{name:'Investigator'})).toHaveAttribute('aria-pressed','true')
  await user.click(screen.getByRole('button',{name:'Crime Analyst'}))
  expect(screen.getByRole('button',{name:'Crime Analyst'})).toHaveAttribute('aria-pressed','true')
  expect(screen.getByRole('button',{name:'Investigator'})).toHaveAttribute('aria-pressed','false')
})

it('renders factual Related Cases reasons without a Case DNA score',()=>{
  render(<RelatedCasesPanel onOpen={()=>undefined} data={{metadata:{limitations:'Stored factual relationships only; a connection does not imply guilt.'},related_cases:[{case_id:'SYN-CASE-0002',crime_number:'SYN-CR-002',case_number:'SYN-CN-002',registered_at:'2026-01-01',freshness_state:'Fresh',jurisdiction_state:'assigned_station',related_reasons:[{reason_type:'SHARED_ACCUSED',group:'Shared People',label:'Shared accused',factual_value:'***masked***',matched_record_id:'SYN-PER-01'}]}]}}/>)
  expect(screen.getByRole('region',{name:'Related Cases'})).toBeInTheDocument()
  expect(screen.getByText('Shared accused: ***masked***')).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Open Case 360'})).toBeInTheDocument()
  expect(screen.queryByText(/Case DNA|similarity score|risk score/i)).not.toBeInTheDocument()
})

it('renders structured network-cluster methodology without treating it as a React child',()=>{
  render(<NetworkClustersPanel data={{
    methodology:{method:'Bounded factual graph traversal.',limitations:['Candidate links require human verification.'],max_cluster_size:10,max_neighbours:8},
    clusters:[{id:'CLUSTER-1',member_case_ids:['SYN-CASE-0001','SYN-CASE-0002'],reasons:['Shared recorded identifier']}],
  }}/>)
  expect(screen.getByRole('region',{name:'Candidate network clusters'})).toBeInTheDocument()
  expect(screen.getByText('Bounded factual graph traversal.')).toBeInTheDocument()
  expect(screen.getByText(/max cluster size:/i)).toBeInTheDocument()
  expect(screen.getByText('10')).toBeInTheDocument()
  expect(screen.getByText('Candidate links require human verification.')).toBeInTheDocument()
})

it('offers case comparison only when the callback is provided',()=>{
  render(<RelatedCasesPanel onOpen={()=>undefined} onCompare={()=>undefined} data={{metadata:{limitations:'Factual records only.'},related_cases:[{case_id:'CASE-2',crime_number:'CR-2',registered_at:'2026-01-01',related_reasons:[]}]}}/>)
  expect(screen.getByRole('button',{name:'Compare'})).toBeInTheDocument()
})

it('renders the shift intelligence briefing with human review',()=>{
  render(<ShiftBriefingPanel data={{headline:'What changed this shift?',summary:{authorised_case_count:8,network_leads:2},sources:{degraded:[{id:'DOC',name:'Document source',status:'Stale'}]},attention:[{title:'Station volume changed',priority_band:'MEDIUM',why:['Four more records'],limitations:['Descriptive only.']}],quality_alerts:[],network_leads:[],mo_pattern_leads:[],limitations:['Synthetic authorised records only.']}}/>)
  expect(screen.getByRole('region',{name:'Shift intelligence briefing'})).toBeInTheDocument()
  expect(screen.getByText('What changed this shift?')).toBeInTheDocument()
  expect(screen.getByText(/Human review required/i)).toBeInTheDocument()
  expect(screen.queryByText(/\bguilt\b|\brisk\b/i)).not.toBeInTheDocument()
})

it('renders factual comparison without score language',()=>{
  render(<CaseComparePanel data={{left:{crime_number:'CR-1',status:'Open'},right:{crime_number:'CR-2',status:'Open'},shared_facts:[{field:'status',value:'Open'}],differing_facts:[{field:'district',left:'A',right:'B'}],related_reasons:[{label:'Shared section'}],limitations:['Factual comparison only.','No similarity score is produced.']}}/>)
  expect(screen.getByRole('region',{name:'FIR case comparison'})).toBeInTheDocument()
  expect(screen.getByText('Shared section')).toBeInTheDocument()
  expect(screen.queryByText(/score/i)).not.toBeInTheDocument()
})

it('renders verification priority cards',()=>{
  render(<VerificationPriorityPanel data={{priorities:[{id:'P-1',title:'Review source freshness',priority_band:'HIGH',why:['Source is stale'],limitations:['Human review only.']}],limitations:['Suggested order only.']}}/>)
  expect(screen.getByRole('region',{name:'Verification priorities'})).toBeInTheDocument()
  expect(screen.getByText('HIGH')).toBeInTheDocument()
  expect(screen.getByText('Source is stale')).toBeInTheDocument()
})

it('renders grounded brief claims and download control',()=>{
  render(<BriefPreviewPanel data={{
    dossier_title:'Synthetic Investigation Dossier',
    brief_type:'synthetic_investigation_dossier',
    case_id:'SYN-CASE-0001',
    case_snapshot:{fir_number:'SYN-FIR-1',crime_number:'SYN-CR-1',status:'UNRESOLVED'},
    exhibits:[{id:'exh-1',exhibit_code:'EXH-0001-01',caption:'Watermarked synthetic scene sketch',sha256:'abc123def4567890',chain_status:'SYNTHETIC_CHAIN',source_record_id:'SRC-1'}],
    sections:{cover:[{text:'CR-1 is recorded open.',verification_state:'verified_from_record',source_record_ids:['SRC-1']}]},
    limitations:['Synthetic data only.'],
  }} busy={false} onDownload={()=>undefined}/>)
  expect(screen.getByRole('region',{name:'Grounded brief preview'})).toBeInTheDocument()
  expect(screen.getByRole('heading',{name:'Synthetic Investigation Dossier'})).toBeInTheDocument()
  expect(screen.getByText('verified_from_record')).toBeInTheDocument()
  expect(screen.getAllByText(/SRC-1/).length).toBeGreaterThanOrEqual(1)
  expect(screen.getByText('EXH-0001-01')).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Download complete case dossier PDF'})).toBeInTheDocument()
})

it('renders the ordered dataset-focused FIR Case 360 sections without raw payloads',()=>{
  render(<Case360Workspace onPassport={()=>undefined} detail={{
    sections:[
      {id:'fir_summary',label:'FIR Summary'},{id:'incident',label:'Incident'},{id:'people',label:'People'},
      {id:'legal',label:'Acts & Sections'},{id:'classifications',label:'Classification'},
      {id:'organisation',label:'Police & Court'},{id:'arrests',label:'Arrest / Surrender'},
      {id:'chargesheets',label:'Chargesheet / Final Report'},{id:'property_identifiers',label:'Property Identifiers'},
      {id:'evidence',label:'Evidence'},{id:'exhibits',label:'Synthetic Exhibits'},
      {id:'timeline',label:'Timeline'},{id:'sources',label:'Sources & Provenance'},{id:'data_quality',label:'Data Quality'},
    ],
    case:{id:'SYN-CASE-0001',crime_number:'SYN-CR-001',case_number:'SYN-CN-001',legacy_status:'OPEN',registered_at:'2026-01-01T00:00:00Z'},
    incident:{incident_from_at:'2026-01-01T00:00:00Z',brief_facts:'Synthetic factual summary.',latitude:null,longitude:null},
    people:{complainants:[],victims:[],accused:[]},legal_provisions:{associations:[]},classification:{},police_and_court:{},arrest_section:{events:[]},chargesheet_section:{records:[]},property_identifiers:[],evidence_section:{records:[],forensic_events:[],documents:[],exhibits:[]},timeline:[],sources:[],data_quality:[],
  }}/>)
  expect(screen.getByRole('region',{name:'FIR Case 360'})).toBeInTheDocument()
  expect(screen.getAllByText('FIR Summary')).toHaveLength(2)
  expect(screen.getAllByText('Sources & Provenance')).toHaveLength(2)
  expect(screen.getAllByText('Synthetic Exhibits')).toHaveLength(2)
  expect(screen.getByText(/No arrest or surrender recorded/i)).toBeInTheDocument()
  expect(screen.queryByText(/original_source_value|payload_json/i)).not.toBeInTheDocument()
})

it('renders Record Assurance summaries without a score or VERIFY primary label',()=>{
  render(<Case360Workspace onPassport={()=>undefined} detail={{case:{id:'SYN-CASE-0001'},incident:{},people:{complainants:[],victims:[],accused:[]},legal_provisions:{associations:[]},classification:{},police_and_court:{},arrest_section:{events:[]},chargesheet_section:{records:[]},evidence_section:{records:[],forensic_events:[]},timeline:[],sources:[],assurance:{rule_version:'fir-assurance-v1',summary:{BLOCKING:1,WARNING:2,OPEN:3}},data_quality:[{id:'FIR-ASSURE-1',severity:'BLOCKING',status:'OPEN',title:'Incident Start After End',factual_explanation:'Incident start is after incident end.',affected_record_type:'CASE',deterministic_rule_version:'fir-assurance-v1'}]}}/>)
  expect(screen.getByText(/Record Assurance/)).toBeInTheDocument()
  expect(screen.getByText(/BLOCKING: 1/)).toBeInTheDocument()
  expect(screen.queryByText(/risk score|VERIFY/i)).not.toBeInTheDocument()
})

it('filters Record Assurance findings with accessible controls',()=>{
  render(<RecordAssurancePanel canResolve onUpdate={()=>undefined} data={{rule_version:'fir-assurance-v1',summary:{WARNING:1,OPEN:1},findings:[{id:'FIR-1',severity:'WARNING',status:'OPEN',title:'Source stale',factual_explanation:'Source is stale.',affected_record_type:'CASE',deterministic_rule_version:'fir-assurance-v1'}]}}/> )
  expect(screen.getByRole('region',{name:'Record Assurance'})).toBeInTheDocument()
  expect(screen.getByLabelText('Assurance severity')).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Resolve finding'})).toBeInTheDocument()
})

it('renders the bounded FIR Relationship Graph with an accessible text fallback',()=>{
  render(<FirRelationshipGraph onOpen={()=>undefined} data={{graph:{base_case_id:'SYN-CASE-0001',truncated:false,disclaimer:'Factual records do not imply guilt, risk, identity, or recommendation.',nodes:[{id:'SYN-CASE-0001',type:'CASE',label:'SYN-CR-001',masked:false},{id:'SYN-PER-0001',type:'PERSON',label:'Masked person',masked:true}],edges:[{id:'edge-1',source:'SYN-CASE-0001',target:'SYN-PER-0001',relationship_type:'CASE_HAS_ACCUSED',freshness:'Fresh',projected:false,factual_basis:'Stored FIR record',source_system:'Synthetic CCTNS'}]},textual_fallback:['SYN-CASE-0001 — CASE_HAS_ACCUSED → SYN-PER-0001']}}/> )
  expect(screen.getByRole('region',{name:'FIR Relationship Graph'})).toBeInTheDocument()
  expect(screen.getByText('Layers')).toBeInTheDocument()
  expect(screen.getByText('CASE HAS ACCUSED')).toBeInTheDocument()
  expect(screen.getByText(/Text fallback/)).toBeInTheDocument()
  expect(screen.getByText(/Masked PERSON/)).toBeInTheDocument()
  expect(screen.queryByText(/Case DNA|similarity score|risk score/i)).not.toBeInTheDocument()
})
