const users = {
  'investigator.demo': { id: 'SYN-USR-INV', username: 'investigator.demo', role: 'INVESTIGATOR', assigned_station: 'SYN-STN-01', assigned_district: 'SYN-DIST-01' },
  'analyst.demo': { id: 'SYN-USR-CA', username: 'analyst.demo', role: 'CRIME_ANALYST', assigned_station: 'SYN-STN-02', assigned_district: 'SYN-DIST-01' },
  'supervisor.demo': { id: 'SYN-USR-SUP', username: 'supervisor.demo', role: 'SUPERVISOR', assigned_station: 'SYN-STN-HQ', assigned_district: 'SYN-DIST-01' },
}

const sources = [
  { id: 'CCTNS_REPLICA', name: 'CCTNS Replica', status: 'Fresh', selectable: true },
  { id: 'SCR_SUMMARY', name: 'SCR Summary (Encrypted)', status: 'Fresh', selectable: true },
  { id: 'ICJS_CRIME', name: 'ICJS Crime Index', status: 'Stale', selectable: true },
]

const investigations = {}
let invCounter = 0
let msgCounter = 0
let convCounter = 0

const mockCases = [
  { case_id: 'SYN-CASE-0001', crime_number: 'SYN-CRIME-00001', offence: 'CHAIN_SNATCHING', status: 'UNRESOLVED', canonical_status: { name: 'Unresolved' }, police_unit: { name: 'SYN-STN-01' }, registered_at: '2026-05-15', source_system: 'CCTNS_REPLICA' },
  { case_id: 'SYN-CASE-0002', crime_number: 'SYN-CRIME-00002', offence: 'ROBBERY', status: 'UNRESOLVED', canonical_status: { name: 'Unresolved' }, police_unit: { name: 'SYN-STN-01' }, registered_at: '2026-06-20', source_system: 'CCTNS_REPLICA' },
  { case_id: 'SYN-CASE-0003', crime_number: 'SYN-CRIME-00003', offence: 'BURGLARY', status: 'RESOLVED', canonical_status: { name: 'Resolved' }, police_unit: { name: 'SYN-STN-02' }, registered_at: '2026-04-10', source_system: 'CCTNS_REPLICA' },
  { case_id: 'SYN-CASE-0004', crime_number: 'SYN-CRIME-00004', offence: 'CHAIN_SNATCHING', status: 'UNRESOLVED', canonical_status: { name: 'Unresolved' }, police_unit: { name: 'SYN-STN-01' }, registered_at: '2026-07-01', source_system: 'CCTNS_REPLICA' },
  { case_id: 'SYN-CASE-0005', crime_number: 'SYN-CRIME-00005', offence: 'VEHICLE_THEFT', status: 'UNRESOLVED', canonical_status: { name: 'Unresolved' }, police_unit: { name: 'SYN-STN-03' }, registered_at: '2026-07-12', source_system: 'CCTNS_REPLICA' },
]

const case360Detail = {
  case: { id: 'SYN-CASE-0001', crime_number: 'SYN-CRIME-00001', offence: 'CHAIN_SNATCHING', status: 'UNRESOLVED', fir_date: '2026-05-15', station: 'SYN-STN-01' },
  overview: { id: 'SYN-CASE-0001', fir_number: 'SYN-CRIME-00001', registered_at: '2026-05-15', crime_category: 'Property Offence' },
  complainant: { name: 'Ravi Kumar', relation: 'Self' },
  people: {
    complainants: [{ person_id: 'P1', display_name: 'Ravi Kumar', role: 'COMPLAINANT', age: 42 }],
    victims: [{ person_id: 'P2', display_name: 'Sneha R', role: 'VICTIM', age: 28 }],
    accused: [{ person_id: 'P3', display_name: 'Unknown Accused', role: 'ACCUSED', age: null }],
    witnesses: [{ person_id: 'P4', display_name: 'Anita S', role: 'WITNESS', age: 35, statement_text: 'Saw two persons on a motorcycle snatch a chain and flee towards south.' }],
  },
  evidence: [
    { id: 'E1', type: 'CCTV Footage', description: 'CCTV from Jayanagar 4th Block', status: 'COLLECTED' },
    { id: 'E2', type: 'Witness Statement', description: 'Statement of Anita S', status: 'RECORDED' },
  ],
  statements: [{ id: 'S1', display_name: 'Anita S', statement_text: 'Saw two persons on a motorcycle snatch a chain and flee towards south.' }],
  sections: [
    { id: 'summary', label: 'Summary', type: 'summary' },
    { id: 'people', label: 'People', type: 'people' },
  ],
  police_and_court: { unit_name: 'SYN-STN-01', investigating_officer: { display_name: 'Inspector Mahesh' }, court_name: 'Karnataka Sessions Court' },
  acts_sections: [{ act: 'IPC', section: '379', description: 'Theft' }, { act: 'IPC', section: '356', description: 'Assault or criminal force' }],
  timeline: [{ date: '2026-05-15', event: 'FIR Registered' }, { date: '2026-05-16', event: 'CCTV collected' }],
  assurance: { summary: { total_findings: 2, resolved: 0 }, findings: [{ id: 'F1', description: 'CCTV footage not yet analyzed', status: 'OPEN', severity: 'medium' }, { id: 'F2', description: 'Witness statement needs verification', status: 'OPEN', severity: 'low' }] },
}

const mockBriefing = {
  headline: 'Shift Briefing — 25 July 2026',
  summary: { authorised_case_count: 12, period: 'Last 24 hours' },
  attention: [{ id: 'A1', description: 'Chain snatching spike in SYN-STN-01 jurisdiction', priority: 'HIGH' }],
  quality_alerts: [{ id: 'Q1', description: '3 cases missing suspect details', severity: 'MEDIUM' }],
  network_leads: [],
  mo_pattern_leads: [{ pattern: 'NIGHT + TWO_WHEELER', count: 4 }],
  limitations: ['Synthetic data only'],
  sources: { degraded: [] },
}

const mockTrends = {
  summary: { authorised_case_count: 48, earliest_month: '2026-01', latest_month: '2026-07' },
  monthly_incidents: [
    { month: '2026-01', count: 5 }, { month: '2026-02', count: 7 }, { month: '2026-03', count: 6 },
    { month: '2026-04', count: 8 }, { month: '2026-05', count: 10 }, { month: '2026-06', count: 7 },
    { month: '2026-07', count: 5 },
  ],
  station_hotspots: [{ station_id: 'SYN-STN-01', count: 18 }, { station_id: 'SYN-STN-02', count: 12 }],
  offence_distribution: [{ offence: 'CHAIN_SNATCHING', count: 15 }, { offence: 'ROBBERY', count: 10 }],
  seasonal_month_of_year: [{ month_of_year: 7, label: 'July', count: 5 }],
  mo_cooccurrence: [{ left: 'NIGHT', right: 'TWO_WHEELER', count: 8 }],
  methodology: { method: 'Descriptive aggregation', limitations: ['Not a forecast'] },
}

function ok(data, warnings = []) {
  return new Response(JSON.stringify({ request_id: `req-${Date.now()}`, data, warnings }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-ZCSRF-TOKEN' },
  })
}

function okWithCookie(data, cookieValue, warnings = []) {
  return new Response(JSON.stringify({ request_id: `req-${Date.now()}`, data, warnings }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-ZCSRF-TOKEN', 'Set-Cookie': `anvaya_session=${cookieValue}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400` },
  })
}

function notFound(msg = 'Not found') {
  return new Response(JSON.stringify({ message: msg, retryable: false }), {
    status: 404,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  })
}

function badRequest(msg) {
  return new Response(JSON.stringify({ message: msg, retryable: false }), {
    status: 400,
    headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
  })
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type,X-ZCSRF-TOKEN' } })
}

export async function GET(request) {
  const { pathname, searchParams } = new URL(request.url)
  const segments = pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean)

  if (pathname === '/api/health' || pathname === '/api/health/') {
    return ok({ status: 'ok', service: 'anvaya-api', environment: 'vercel-mock', database: 'ok', public_demo_enabled: true, ai_assist_enabled: true, voice_enabled: false })
  }

  if (pathname === '/api/auth/session' || pathname === '/api/auth/session/') {
    return ok(users['investigator.demo'])
  }

  if (pathname === '/api/source-control' || pathname === '/api/source-control/') {
    return ok({ sources })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'history') {
    return ok([])
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'analytics' && segments[3] === 'trends') {
    return ok(mockTrends)
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'analytics' && segments[3] === 'briefing') {
    return ok(mockBriefing)
  }

  if (segments[0] === 'cases' && segments[1] && segments[2] === '360') {
    return ok(case360Detail)
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'cases' && segments[3]) {
    if (segments[4] === '360') return ok(case360Detail)
    if (segments[4] === 'related') return ok({ cases: mockCases.slice(0, 3) })
    if (segments[4] === 'graph') return ok({ nodes: [], edges: [] })
    if (segments[4] === 'network-clusters') return ok({ clusters: [{ label: 'Cluster 1', count: 3, members: ['SYN-CASE-0001', 'SYN-CASE-0002', 'SYN-CASE-0004'] }] })
    if (segments[4] === 'priorities') return ok({ priorities: [{ case_id: 'SYN-CASE-0001', score: 85, reason: 'Unresolved chain snatching with CCTV evidence' }] })
    if (segments[4] === 'assurance') {
      if (segments[5]) return ok({ updated: true })
      return ok(case360Detail.assurance)
    }
    if (segments[4] === 'brief') {
      if (pathname.endsWith('.pdf')) {
        return new Response('Mock PDF content', { status: 200, headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename="brief.pdf"` } })
      }
      return ok({ title: 'Investigation Dossier', case_id: segments[3], sections: [{ heading: 'Summary', content: 'Mock dossier summary for demo purposes.' }] })
    }
    if (segments[4] === 'graph' && segments[5] === 'path') return ok({ path: [] })
    if (segments[4] === 'compare' && segments[5]) return ok({ comparison: [] })
  }

  if (segments[0] === 'source-passports' && segments[1]) {
    return ok({ id: segments[1], name: 'Source Passport', status: 'Verified', source_records: [{ id: 'SRC-1', type: 'CCTNS', status: 'Fresh' }] })
  }

  if (pathname === '/api/reports' || pathname === '/api/reports/') {
    return ok({ reports: [] })
  }

  if (segments[0] === 'reports' && segments[1]) {
    const sub = segments[2]
    if (sub === 'preview') return ok({ html: '<html><body><h1>Report Preview</h1><p>Mock preview content.</p></body></html>' })
    if (sub === 'preview-metadata') return ok({ filename: `report-${segments[1]}.pdf`, pages: 5 })
    if (sub === 'versions') return ok({ version_number: 2, status: 'DRAFT' })
    if (sub === 'assign') return ok({ assigned_reviewer_id: 'reviewer-1' })
    if (sub === 'submit') return ok({ status: 'SUBMITTED', report_id: segments[1] })
    if (sub === 'review') return ok({ decision: 'APPROVED' })
    return ok({ report: { report_id: segments[1], title: 'Demo Report', status: 'DRAFT', assigned_reviewer_id: null }, allowed_actions: ['edit', 'submit'], versions: [], review_history: [] })
  }

  if (pathname === '/api/reviewers' || pathname === '/api/reviewers/') {
    return ok([{ username: 'supervisor.demo' }])
  }

  if (pathname === '/api/system-health' || pathname === '/api/system-health/') {
    return ok({ status: 'healthy', backend: 'mock', database: 'mock', migration_version: '1.0', optional_ai: 'disabled', report_export: 'browser print-to-PDF', degraded_mode: false, sources })
  }

  if (pathname.startsWith('/api/audit-events')) {
    return ok({ events: [] })
  }

  if (pathname === '/api/investigation-home' || pathname === '/api/investigation-home/') {
    return ok({ message: 'Welcome' })
  }

  if (pathname === '/api/sources' || pathname === '/api/sources/') {
    return ok(sources)
  }

  if (pathname === '/api/conversations' || pathname === '/api/conversations/') {
    return ok([])
  }

  if (segments[0] === 'conversations' && segments[1] && segments[2] === 'search') {
    return ok([])
  }

  if (segments[0] === 'conversations' && segments[1]) {
    return ok({ id: segments[1], title: 'Demo Conversation', messages: [] })
  }

  if (segments[0] === 'copilot' && segments[1] === 'analyze' && segments[2]) {
    return ok({ suggestions: ['Review CCTV evidence', 'Contact witness'], gaps: ['Suspect description missing'] })
  }

  if (segments[0] === 'copilot' && segments[1] === 'suggest' && segments[2] && segments[3]) {
    return ok({ next_actions: ['Verify alibi', 'Check phone records'] })
  }

  if (segments[0] === 'explain' && segments[1] && segments[2] && segments[3]) {
    return ok({ explanation: 'This finding is based on witness statement S1.', confidence: 0.85 })
  }

  if (segments[0] === 'explain' && segments[1] === 'edge') {
    return ok({ explanation: 'Connection between these entities is based on shared location data.' })
  }

  if (pathname.startsWith('/api/shift/intelligence')) {
    return ok({ station_id: searchParams.get('station') || 'SYN-STN-01', attention_leads: [], officer_workload: [] })
  }

  if (segments[0] === 'supervisor' && segments[1] === 'timeline' && segments[2]) {
    return ok({ events: [] })
  }

  if (segments[0] === 'supervisor' && segments[1] === 'review' && segments[2] && segments[3]) {
    return ok({ review: { id: segments[3], status: 'PENDING' } })
  }

  if (segments[0] === 'm5' && segments[1] === 'graph' && segments[2]) {
    return ok({ nodes: [], edges: [] })
  }

  if (segments[0] === 'm5' && (segments[1] === 'assurance' || segments[1] === 'actions') && segments[2]) {
    return ok({ findings: [] })
  }

  if (segments[0] === 'm5' && segments[1] === 'verify' && segments[2] && segments[3]) {
    return ok({ match_score: 0.65, shared_attributes: ['location', 'time_of_day'] })
  }

  if (pathname.startsWith('/api/relationships/path')) {
    return ok({ path: [] })
  }

  return notFound(`Unknown route: ${pathname}`)
}

export async function POST(request) {
  const { pathname } = new URL(request.url)
  const segments = pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean)
  let body = {}
  try { body = await request.json() } catch { }

  if (pathname === '/api/auth/login' || pathname === '/api/auth/login/') {
    const id = body.role === 'SUPERVISOR' ? 'SYN-USR-SUP' : body.role === 'CRIME_ANALYST' ? 'SYN-USR-CA' : 'SYN-USR-INV'
    const user = { id, username: body.username || 'User', role: body.role || 'INVESTIGATOR', assigned_station: body.station || 'SYN-STN-01', assigned_district: body.district || 'SYN-DIST-01' }
    return okWithCookie(user, 'demo', [{ code: 'DEMO', message: 'Demo mode active. All data is synthetic.' }])
  }

  if (pathname === '/api/auth/public-demo' || pathname === '/api/auth/public-demo/') {
    return okWithCookie(users['investigator.demo'], 'demo', [{ code: 'DEMO', message: 'Public demo mode active. All data is synthetic.' }])
  }

  if (pathname === '/api/auth/logout' || pathname === '/api/auth/logout/') {
    return ok({ logged_out: true })
  }

  if (pathname === '/api/investigations' || pathname === '/api/investigations/') {
    invCounter++
    const inv = { id: `INV-${invCounter}`, title: body.title || 'Investigation', purpose: body.purpose || 'Active Case Investigation', selected_sources: body.selected_sources || ['CCTNS_REPLICA'], assigned_station: 'SYN-STN-01', assigned_district: 'SYN-DIST-01' }
    investigations[inv.id] = inv
    return ok(inv)
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'query' && segments[3] === 'preview') {
    msgCounter++
    const filters = { offence: 'CHAIN_SNATCHING', status: 'UNRESOLVED', location: 'Jayanagar' }
    if (body.query?.toLowerCase().includes('robbery')) filters.offence = 'ROBBERY'
    if (body.query?.toLowerCase().includes('burglary')) filters.offence = 'BURGLARY'
    if (body.query?.toLowerCase().includes('vehicle') || body.query?.toLowerCase().includes('theft')) filters.offence = 'VEHICLE_THEFT'
    return ok({ message_id: `MSG-${msgCounter}`, normalised_interpretation: { intent: 'SEARCH', confidence: 0.87, uncertain_fields: ['location'], filters, selected_sources: ['CCTNS_REPLICA'], result_limit: 25 } })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'query' && segments[3] === 'follow-up') {
    msgCounter++
    return ok({ message_id: `MSG-${msgCounter}`, parent_message_id: body.parent_message_id || '', normalised_interpretation: { intent: 'SEARCH', filters: { offence: 'ROBBERY', status: 'UNRESOLVED', location: 'Jayanagar' }, selected_sources: ['CCTNS_REPLICA'], result_limit: 25 }, inherited_fields: ['offence'] })
  }

  if (segments[0] === 'investigations' && segments[1] && (segments[2] === 'search' || segments[2] === 'discover')) {
    return ok({ results: mockCases })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'sources' && segments[3] === 'preset') {
    return ok(investigations[segments[1]] || { id: segments[1], selected_sources: ['CCTNS_REPLICA'] })
  }

  if (pathname === '/api/query/validate' || pathname === '/api/query/validate/') {
    return ok({ valid: true, warnings: [] })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'conversation.pdf') {
    return new Response('Mock PDF', { status: 200, headers: { 'Content-Type': 'application/pdf' } })
  }

  if (pathname.startsWith('/api/voice/transcribe')) {
    return ok({ text: body.text || 'Demo voice transcript', language: 'en-IN' })
  }

  if (pathname.startsWith('/api/voice/translate')) {
    return ok({ text: body.text || 'Translated text', source_language_code: 'kn-IN', target_language_code: 'en-IN' })
  }

  if (pathname === '/api/voice/speak' || pathname === '/api/voice/speak/') {
    return ok({ audio_base64: '', content_type: 'audio/wav', target_language_code: 'kn-IN' })
  }

  if (pathname === '/api/conversations' || pathname === '/api/conversations/') {
    convCounter++
    return ok({ id: `CONV-${convCounter}`, title: body.title || 'New Conversation', messages: [] })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'chat' && segments[3] === 'action') {
    return ok({ action: 'preview', params: { query: body.query } })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'answer') {
    return ok({ answer: 'Mock AI answer based on available records.', sources: [] })
  }

  if (pathname === '/api/reports' || pathname === '/api/reports/') {
    return ok({ report_id: `RPT-${Date.now()}`, title: body.title || 'New Report', status: 'DRAFT' })
  }

  if (segments[0] === 'reports' && segments[1]) {
    return ok({ updated: true, report_id: segments[1] })
  }

  if (segments[0] === 'supervisor' && segments[1] === 'review' && segments[2]) {
    return ok({ review_id: `REV-${Date.now()}`, status: 'SUBMITTED' })
  }

  if (segments[0] === 'm5' && segments[1] === 'challenge' && segments[2]) {
    return ok({ challenge_id: `CH-${Date.now()}`, result: 'Hypothesis not supported by available evidence.' })
  }

  return notFound(`Unknown POST route: ${pathname}`)
}

export async function PATCH(request) {
  const { pathname } = new URL(request.url)
  const segments = pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean)
  let body = {}
  try { body = await request.json() } catch { }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'sources') {
    const inv = investigations[segments[1]]
    if (inv) { inv.selected_sources = body.selected_sources || inv.selected_sources }
    return ok(inv || { id: segments[1], selected_sources: body.selected_sources || ['CCTNS_REPLICA'] })
  }

  if (segments[0] === 'investigations' && segments[1] && segments[2] === 'cases' && segments[3] && segments[4] === 'assurance' && segments[5]) {
    return ok({ updated: true, finding_id: segments[5], status: body.status })
  }

  if (segments[0] === 'reports' && segments[1]) {
    return ok({ updated: true, report_id: segments[1] })
  }

  if (segments[0] === 'conversations' && segments[1]) {
    return ok({ id: segments[1], ...body })
  }

  return notFound(`Unknown PATCH route: ${pathname}`)
}

export async function DELETE(request) {
  const { pathname } = new URL(request.url)
  const segments = pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean)

  if (segments[0] === 'conversations' && segments[1]) {
    return ok({ deleted: true, id: segments[1] })
  }

  return notFound(`Unknown DELETE route: ${pathname}`)
}
