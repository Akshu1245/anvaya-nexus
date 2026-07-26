import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { m3Api, type HealthStatus, type Investigation, type Source, type User } from '../api/m3'
import { btnOutline, btnPrimary, btnSecondary } from '../components/PortalButtons'
import { PortalModal } from '../components/PortalModal'
import { JourneyStepper, type JourneyStage } from '../components/ui'
import { useLocale } from '../i18n/portal'
import { OffenceBadge, OFFENCE_CATALOGUE } from '../components/OffenceVisual'
import {
  BriefPreviewPanel,
  Case360Workspace,
  CrimeTrendsPanel,
  FirRelationshipGraph,
  NetworkClustersPanel,
  QueryInterpretationPanel,
  RecordAssurancePanel,
  RelatedCasesPanel,
  ShiftBriefingPanel,
  VerificationPriorityPanel,
} from '../features/m4/InvestigationExperience'
import { SourcePassportDrawer } from '../features/m4/SourcePassportDrawer'
import { useAuthStore } from '../stores/authStore'

const emptyFilters = {
  crime_number: '', case_number: '', case_identifier: '', registration_date_from: '', registration_date_to: '',
  date_from: '', date_to: '', person_name: '', person_role: '', act_code: '', section_code: '',
  case_category: '', gravity_offence: '', crime_major_head: '', crime_minor_head: '', canonical_case_status: '',
  arrest_event_type: '', chargesheet_report_type: '', state: '', district: '', police_unit: '', registering_officer: '', court: '',
  offence: '', location: '', status: '',
}

const stageOrder: JourneyStage[] = ['ASK', 'DISCOVER', 'VERIFY', 'PRIORITISE', 'REPORT']
const caseIdOf = (detail: any) => detail?.case?.id || detail?.overview?.id
const GOLDEN_QUERY = 'Find unresolved chain snatching cases near Jayanagar in the last 90 days'
const filterLabelsKn: Record<string, string> = {
  offence: 'ಅಪರಾಧ', status: 'ಸ್ಥಿತಿ', location: 'ಸ್ಥಳ / ಠಾಣೆ', crime_number: 'ಅಪರಾಧ ಸಂಖ್ಯೆ',
  case_number: 'ಪ್ರಕರಣ ಸಂಖ್ಯೆ', date_from: 'ಘಟನೆ ಆರಂಭ', date_to: 'ಘಟನೆ ಅಂತ್ಯ', person_name: 'ವ್ಯಕ್ತಿಯ ಹೆಸರು',
  person_role: 'ವ್ಯಕ್ತಿಯ ಪಾತ್ರ', act_code: 'ಕಾಯ್ದೆ ಕೋಡ್', section_code: 'ಸೆಕ್ಷನ್ ಕೋಡ್', police_unit: 'ಪೊಲೀಸ್ ಘಟಕ', district: 'ಜಿಲ್ಲೆ',
}

function defaultPurpose(role?: User['role']) {
  if (role === 'CRIME_ANALYST') return 'Pattern Research'
  if (role === 'SUPERVISOR') return 'Supervisor Review'
  return 'Active Case Investigation'
}

export function SearchPage() {
  const { locale, t } = useLocale()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)!

  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [control, setControl] = useState<any>(null)
  const [inv, setInv] = useState<Investigation | null>(null)
  const [selected, setSelected] = useState<string[]>(['CCTNS_REPLICA'])
  const [query, setQuery] = useState('')
  const [preview, setPreview] = useState<any>(null)
  const [filters, setFilters] = useState({ ...emptyFilters })
  const [hasArrest, setHasArrest] = useState(false)
  const [hasChargesheet, setHasChargesheet] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [searched, setSearched] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [caseOpen, setCaseOpen] = useState(false)
  const [passport, setPassport] = useState<any>(null)
  const [briefing, setBriefing] = useState<any>(null)
  const [trends, setTrends] = useState<any>(null)
  const [related, setRelated] = useState<any>(null)
  const [graph, setGraph] = useState<any>(null)
  const [clusters, setClusters] = useState<any>(null)
  const [priorities, setPriorities] = useState<any>(null)
  const [brief, setBrief] = useState<any>(null)
  const [briefOpen, setBriefOpen] = useState(false)
  const [stage, setStage] = useState<JourneyStage>('ASK')
  const [maxStage, setMaxStage] = useState<JourneyStage>('ASK')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const isSupervisor = user?.role === 'SUPERVISOR'

  useEffect(() => { void m3Api.health().then(setHealth).catch(() => setHealth({ status: 'ok', service: 'anvaya-api', environment: 'unknown', database: 'ok', public_demo_enabled: false })) }, [])

  const advance = (next: JourneyStage) => { setStage(next); setMaxStage(current => stageOrder.indexOf(next) > stageOrder.indexOf(current) ? next : current) }
  const call = async (label: string, fn: () => Promise<any>) => { setBusy(label); setError(''); try { return await fn() } catch (e) { setError((e as Error).message); return null } finally { setBusy('') } }

  useEffect(() => {
    if (!user) return
    const purpose = defaultPurpose(user?.role)
    void m3Api.sourceControl(isSupervisor ? 'Supervisor Review' : purpose).then(setControl).catch(() => setControl({ sources: [] }))
  }, [user])

  async function ensureInvestigation() {
    if (inv) return inv
    if (isSupervisor) throw new Error(locale === 'kn' ? 'ಮೇಲ್ವಿಚಾರಕರು ವಿಮರ್ಶೆ-ಮಾತ್ರ.' : 'Supervisor Review is review-only.')
    const created = await m3Api.createInvestigation({ title: 'Portal investigation', purpose: defaultPurpose(user?.role), selected_sources: selected.length ? selected : ['CCTNS_REPLICA'] })
    setInv(created)
    setSelected(created.selected_sources)
    return created
  }

  async function doPreview(raw = query) {
    const text = raw.trim(); if (!text) { setError(locale === 'kn' ? 'ಪ್ರಶ್ನೆ ನಮೂದಿಸಿ.' : 'Enter a question.'); return }
    const investigation = await call('preview', () => ensureInvestigation())
    if (!investigation) return
    const value = await call('preview', () => m3Api.preview(investigation.id, text))
    if (value) { setPreview(value); advance('ASK') }
  }

  async function runSearch() {
    if (isSupervisor) { setError('Supervisor Review does not grant search powers.'); return }
    const investigation = await call('search', () => ensureInvestigation())
    if (!investigation) return
    const base = preview?.normalised_interpretation || { intent: 'SEARCH', confidence: 0.5, uncertain_fields: [], selected_sources: selected, result_limit: 25, filters: {} }
    const mergedFilters = {
      ...base.filters,
      ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
      ...(hasArrest ? { has_arrest_event: true } : {}),
      ...(hasChargesheet ? { has_chargesheet: true } : {}),
    }
    const meaningful = Object.values(mergedFilters).some(v => v !== null && v !== undefined && v !== '' && v !== false)
    if (!meaningful && !preview) { setError('Set at least one filter.'); return }
    const plan = { ...base, filters: mergedFilters, selected_sources: selected.length ? selected : base.selected_sources }
    const data = await call('search', () => plan.intent === 'DISCOVER' ? m3Api.discover(investigation.id, plan) : m3Api.search(investigation.id, plan))
    if (!data) return
    setResults(data.results || [])
    setSearched(true)
    advance('DISCOVER')
  }

  async function openCase(caseId: string) {
    const investigation = inv || await call('case', () => ensureInvestigation())
    if (!investigation && !isSupervisor) return
    const purpose = (investigation || inv)?.purpose || defaultPurpose(user?.role)
    const sources = (investigation || inv)?.selected_sources || selected
    const data = await call('case', () => m3Api.case360(caseId, purpose, sources))
    if (data) { setDetail(data); setCaseOpen(true); setRelated(null); setGraph(null); setClusters(null); setPriorities(null); advance('VERIFY') }
  }

  async function loadBriefing() {
    if (isSupervisor) { setError('Supervisor Review does not grant briefing access.'); return }
    const investigation = await call('briefing', () => ensureInvestigation()); if (!investigation) return
    const data = await call('briefing', () => m3Api.briefing(investigation.id))
    if (data) { setBriefing(data); advance('PRIORITISE') }
  }

  async function loadTrends() {
    if (isSupervisor) { setError('Supervisor Review does not grant trends access.'); return }
    const investigation = await call('trends', () => ensureInvestigation()); if (!investigation) return
    const data = await call('trends', () => m3Api.trends(investigation.id))
    if (data) { setTrends(data); advance('PRIORITISE') }
  }

  async function showRelated(caseId: string) { if (!inv) return; const data = await call('related', () => m3Api.related(inv.id, caseId)); if (data) { setRelated(data); advance('PRIORITISE') } }
  async function showGraph(caseId: string) { if (!inv) return; const data = await call('graph', () => m3Api.firGraph(inv.id, caseId)); if (data) { setGraph(data); advance('PRIORITISE') } }
  async function showClusters(caseId: string) { if (!inv) return; const data = await call('clusters', () => m3Api.networkClusters(inv.id, caseId)); if (data) { setClusters(data); advance('PRIORITISE') } }
  async function showPriorities(caseId: string) { if (!inv) return; const data = await call('priorities', () => m3Api.priorities(inv.id, caseId)); if (data) { setPriorities(data); advance('PRIORITISE') } }
  async function prepareBrief(caseId: string) { if (!inv) return; const data = await call('brief', () => m3Api.brief(inv.id, caseId)); if (data) { setBrief(data); setBriefOpen(true); advance('REPORT') } }
  async function downloadBriefPdf() { if (!inv || !detail) return; const id = caseIdOf(detail); await call('brief-pdf', () => m3Api.briefPdf(inv.id, id)) }

  const openPassport = (id: string) => void call('passport', () => m3Api.passport(id, inv?.purpose || defaultPurpose(user?.role))).then(v => v && setPassport(v))

  const onJourney = (next: JourneyStage) => {
    setStage(next)
    if (next === 'VERIFY' && detail) setCaseOpen(true)
    if (next === 'PRIORITISE') { if (briefing) navigate('/dashboard/analytics?tab=briefing'); else if (trends) navigate('/dashboard/analytics?tab=trends') }
    if (next === 'REPORT' && brief) setBriefOpen(true)
  }

  const workspaceSection = 'search'
  const hasVisibleFilters = Object.values(filters).some(Boolean) || hasArrest || hasChargesheet
  const searchReady = Boolean(preview) || hasVisibleFilters
  const clearSearch = () => { setQuery(''); setFilters({ ...emptyFilters }); setHasArrest(false); setHasChargesheet(false); setPreview(null); setError('') }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">{user.role} &middot; {user.assigned_station || '—'} &middot; {user.assigned_district || '—'}</p>
          <h1 className="text-xl font-bold text-navy-950">{locale === 'kn' ? 'ಹುಡುಕಾಟ' : 'Search & Case 360'}</h1>
        </div>
      </div>

      <div className="z-30 sm:sticky sm:top-8"><JourneyStepper current={stage} maxReached={maxStage} onSelect={onJourney} /></div>

      {error && <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"><span>{error}</span><button type="button" className={btnOutline} onClick={() => setError('')}>{t('close')}</button></div>}
      {busy && <p role="status" className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-600">{t('loading')} — {busy}</p>}

      {isSupervisor && <aside className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Supervisor Review is review-only in this prototype.</aside>}

      {!isSupervisor && <section className="space-y-5" aria-label="Search workspace">
        <aside className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-teal-200 bg-teal-50 p-4">
          <div>
            <p className="font-medium text-teal-900">{locale === 'kn' ? 'ಹೊಸದಾಗಿ ಬಂದಿರಾ? ಸಿದ್ಧಪಡಿಸಿದ ಡೆಮೊ ಪ್ರಶ್ನೆಯಿಂದ ಪ್ರಾರಂಭಿಸಿ.' : 'New here? Start with the prepared demo query.'}</p>
            <p className="text-xs text-teal-700">{locale === 'kn' ? 'ಇದು ವ್ಯಾಖ್ಯಾನವನ್ನು ಮಾತ್ರ ಸಿದ್ಧಪಡಿಸುತ್ತದೆ.' : 'This prepares the interpretation only.'}</p>
          </div>
          <button type="button" className={btnSecondary} disabled={Boolean(busy)} onClick={() => { setQuery(GOLDEN_QUERY); setFilters({ ...emptyFilters }); setHasArrest(false); setHasChargesheet(false); setPreview(null); void doPreview(GOLDEN_QUERY) }}>{busy === 'preview' ? t('loading') : (locale === 'kn' ? 'ಡೆಮೊ ಪ್ರಶ್ನೆ ಪ್ರಯತ್ನಿಸಿ' : 'Try demo query')}</button>
        </aside>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">{locale === 'kn' ? 'ಹಂತ 1 &middot; ಕೇಳಿ' : 'Step 1 &middot; Ask'}</p>
          <h3 className="mt-1 text-lg font-semibold text-navy-950">{t('searchTitle')}</h3>
          <label className="mt-4 block text-sm font-medium">{locale === 'kn' ? 'ಪ್ರಶ್ನೆ (ಐಚ್ಛಿಕ)' : 'Question (optional)'}
            <textarea aria-label="Investigation question" className="mt-1 min-h-20 w-full rounded-lg border border-slate-200 p-3 transition focus:border-teal-400 focus:ring-1 focus:ring-teal-400" value={query} onChange={e => { setQuery(e.target.value); setPreview(null) }} placeholder={locale === 'kn' ? 'ಉದಾ. ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ SYN-STN-01' : 'e.g. unresolved chain snatching near SYN-STN-01'} />
          </label>
          <div className="mt-4 flex flex-wrap gap-2">
            {OFFENCE_CATALOGUE.map(item => <button key={item.code} type="button" className={btnOutline + ' !text-xs'} onClick={() => { setFilters(f => ({ ...f, offence: item.label, status: 'UNRESOLVED' })); setQuery(`Find unresolved ${item.label.toLowerCase()} cases`); setPreview(null) }}>{locale === 'kn' ? item.labelKn : item.label}</button>)}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
            <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={() => void runSearch()}>{busy === 'search' ? t('loading') : (locale === 'kn' ? 'ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ' : 'Search records')}</button>
            <button type="button" className={btnSecondary} disabled={Boolean(busy) || !query.trim()} onClick={() => void doPreview(query)}>{busy === 'preview' ? t('loading') : (locale === 'kn' ? 'ಪ್ರಶ್ನೆ ಪೂರ್ವವೀಕ್ಷಣೆ' : 'Preview query')}</button>
            <button type="button" className={btnOutline} disabled={Boolean(busy)} onClick={clearSearch}>{locale === 'kn' ? 'ಅಳಿಸಿ' : 'Clear'}</button>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-wider text-teal-700">{locale === 'kn' ? 'ಹಂತ 2 &middot; ವ್ಯಾಪ್ತಿಯನ್ನು ಹೊಂದಿಸಿ' : 'Step 2 &middot; Set the scope'}</p>
          <h3 className="mt-1 font-semibold">{t('filtersTitle')}</h3>
          <p className="mt-1 text-xs text-slate-500">{t('purposeLabel')}: {inv?.purpose || defaultPurpose(user.role)}</p>
          <fieldset className="mt-3 grid gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
            {([['offence', 'Offence'], ['status', 'Status'], ['location', 'Location / station'], ['crime_number', 'Crime number'], ['case_number', 'Case number'], ['date_from', 'Incident from'], ['date_to', 'Incident to'], ['person_name', 'Person name'], ['person_role', 'Person role'], ['act_code', 'Act code'], ['section_code', 'Section code'], ['police_unit', 'Police unit'], ['district', 'District']] as const).map(([key, label]) => {
              const active = Boolean((filters as any)[key])
              const visibleLabel = locale === 'kn' ? filterLabelsKn[key] || label : label
              return <label key={key} className="flex flex-col text-sm"><span className="mb-1 font-medium text-slate-600">{visibleLabel}</span><input aria-label={visibleLabel} className={`w-full rounded-lg border p-2 transition focus:border-teal-400 focus:ring-1 focus:ring-teal-400 ${active ? 'border-teal-400 bg-teal-50/40' : 'border-slate-200'}`} value={(filters as any)[key]} onChange={e => setFilters({ ...filters, [key]: e.target.value })} /></label>
            })}
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm has-[:checked]:border-teal-400 has-[:checked]:bg-teal-50/40"><input type="checkbox" checked={hasArrest} onChange={e => setHasArrest(e.target.checked)} /> {locale === 'kn' ? 'ಬಂಧನ / ಶರಣಾಗತಿ ಇದೆ' : 'Has arrest / surrender'}</label>
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm has-[:checked]:border-teal-400 has-[:checked]:bg-teal-50/40"><input type="checkbox" checked={hasChargesheet} onChange={e => setHasChargesheet(e.target.checked)} /> {locale === 'kn' ? 'ದೋಷಾರೋಪ ಪಟ್ಟಿ ಇದೆ' : 'Has chargesheet'}</label>
          </fieldset>
          <div className="mt-4">
            <p className="text-sm font-semibold">{t('sourcesLabel')}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(control?.sources || []).filter((s: Source) => s.selectable !== false).map((s: Source) => <label key={s.id} className="rounded border px-2 py-1 text-xs"><input type="checkbox" checked={selected.includes(s.id)} onChange={e => { const next = e.target.checked ? [...selected, s.id] : selected.filter(id => id !== s.id); setSelected(next); if (inv) void m3Api.updateSources(inv.id, next).then(setInv) }} /> {s.name || s.id}</label>)}
              {!control?.sources?.length && <label className="rounded border px-2 py-1 text-xs"><input type="checkbox" checked={selected.includes('CCTNS_REPLICA')} onChange={() => undefined} /> CCTNS_REPLICA</label>}
            </div>
          </div>
        </div>

        {preview && <div className="space-y-2"><p className="text-xs font-bold uppercase tracking-wider text-teal-700">{locale === 'kn' ? 'ಹಂತ 3 &middot; ಪರಿಶೀಲಿಸಿ' : 'Step 3 &middot; Review the interpretation'}</p><QueryInterpretationPanel preview={preview} onChange={setPreview} /></div>}

        <div className="rounded-xl border border-teal-200 bg-white p-4 shadow-sm">
          <p id="search-action-help" className="mb-3 text-sm text-slate-600">{preview ? (locale === 'kn' ? 'ವ್ಯಾಖ್ಯಾನ ಸಿದ್ಧವಾಗಿದೆ.' : 'Interpretation ready.') : hasVisibleFilters ? (locale === 'kn' ? 'ಗೋಚರ ಫಿಲ್ಟರ್‌ಗಳು ಸಿದ್ಧವಾಗಿವೆ.' : 'Filters ready.') : (locale === 'kn' ? 'ಪ್ರಶ್ನೆಯನ್ನು ಪೂರ್ವವೀಕ್ಷಿಸಿ ಅಥವಾ ಕನಿಷ್ಠ ಒಂದು ಫಿಲ್ಟರ್ ಹೊಂದಿಸಿ.' : 'Preview your question or set at least one filter.')}</p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button type="button" className={`${btnPrimary} order-1 w-full justify-center sm:order-2 sm:w-auto`} disabled={Boolean(busy) || !searchReady} onClick={() => void runSearch()}>{busy === 'search' ? t('loading') : <>{t('searchRecords')} <span aria-hidden>→</span></>}</button>
            <div className="order-2 flex flex-wrap gap-2 sm:order-1">
              <button type="button" className={btnSecondary} disabled={Boolean(busy) || !query.trim()} onClick={() => void doPreview()}>{busy === 'preview' ? t('loading') : t('previewQuery')}</button>
              <button type="button" className={btnOutline} disabled={Boolean(busy)} onClick={clearSearch}>{t('clear')}</button>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold">{t('resultsTitle')}</h3>
            {searched && busy !== 'search' && <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700">{results.length} {locale === 'kn' ? 'ದಾಖಲೆಗಳು' : results.length === 1 ? 'record' : 'records'}</span>}
          </div>
          {busy === 'search' ? <div className="mt-3 grid gap-3" role="status" aria-live="polite">
            {[0, 1, 2].map(i => <div key={i} className="rounded-lg border border-slate-200 p-4">
              <div className="h-4 w-2/5 rounded bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer" />
              <div className="mt-3 flex gap-2"><div className="h-5 w-24 rounded-full bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer" /><div className="h-5 w-16 rounded-full bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer" /></div>
              <div className="mt-3 h-3 w-3/5 rounded bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer" />
            </div>)}
          </div> : !searched ? <p className="mt-2 text-sm text-slate-500">{t('resultsEmpty')}</p> :
            results.length === 0 ? <p className="mt-2 text-sm text-amber-800">{locale === 'kn' ? 'ಯಾವುದೇ ದಾಖಲೆ ಸಿಗಲಿಲ್ಲ.' : 'No records matched.'}</p> :
              <div className="mt-3 grid gap-3">
                {results.map((item: any) => <article key={item.case_id || item.id} className="rounded-lg border border-slate-200 p-4 transition hover:border-teal-400 hover:shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-navy-950">{item.crime_number || item.fir_number} &middot; {item.case_number || item.case_id}</p>
                      <div className="mt-1 flex flex-wrap gap-2"><OffenceBadge offence={item.offence || item.category?.name} /><span className="text-xs text-slate-600">{item.canonical_status?.name || item.status}</span></div>
                      <p className="mt-1 text-xs text-slate-500">{item.police_unit?.name || item.station_id} &middot; {item.registered_at}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" className={btnPrimary} onClick={() => void openCase(item.case_id || item.id)}>{t('openCase360')} <span aria-hidden>→</span></button>
                    </div>
                  </div>
                </article>)}
              </div>}
        </div>
      </section>}

      <div className="mt-6 space-y-4">
        <div className="flex flex-wrap gap-2">
          <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={() => void loadBriefing()}>{busy === 'briefing' ? t('loading') : t('loadBriefing')}</button>
          <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={() => void loadTrends()}>{busy === 'trends' ? t('loading') : t('loadTrends')}</button>
        </div>
        {briefing && <ShiftBriefingPanel data={briefing} />}
        {trends && <CrimeTrendsPanel data={trends} />}
      </div>

      {caseOpen && detail && <PortalModal variant="drawer" title={`Case 360 · ${caseIdOf(detail)}`} onClose={() => setCaseOpen(false)}>
        <div className="mb-4 flex flex-wrap gap-2">
          <button type="button" className={btnOutline} onClick={() => void showRelated(caseIdOf(detail))}>{t('related')}</button>
          <button type="button" className={btnOutline} onClick={() => void showGraph(caseIdOf(detail))}>{t('graph')}</button>
          <button type="button" className={btnOutline} onClick={() => void showClusters(caseIdOf(detail))}>{t('networkClusters')}</button>
          <button type="button" className={btnOutline} onClick={() => void showPriorities(caseIdOf(detail))}>{t('priorities')}</button>
          <button type="button" className={btnPrimary} onClick={() => void prepareBrief(caseIdOf(detail))}>{t('prepareBrief')}</button>
        </div>
        <Case360Workspace detail={detail} onPassport={openPassport} />
        {related && <div className="mt-4"><RelatedCasesPanel data={related} onOpen={id => void openCase(id)} /></div>}
        {graph && <div className="mt-4"><FirRelationshipGraph data={graph} onOpen={id => void openCase(id)} /></div>}
        {clusters && <div className="mt-4"><NetworkClustersPanel data={clusters} /></div>}
        {priorities && <div className="mt-4"><VerificationPriorityPanel data={priorities} /></div>}
        {detail.assurance && <div className="mt-4"><RecordAssurancePanel data={detail.assurance} canResolve={user.role === 'SUPERVISOR'} onUpdate={(findingId, status) => { const id = caseIdOf(detail); if (!inv) return; void call('assurance', () => m3Api.updateFirAssurance(inv.id, id, findingId, { status })).then(() => m3Api.firAssurance(inv.id, id)).then(data => data && setDetail({ ...detail, assurance: data })) }} /></div>}
      </PortalModal>}

      {briefOpen && brief && <PortalModal variant="modal" title={t('downloadDossier')} onClose={() => setBriefOpen(false)}>
        <BriefPreviewPanel data={brief} busy={busy === 'brief-pdf'} onDownload={() => void downloadBriefPdf()} />
      </PortalModal>}

      {passport && <SourcePassportDrawer passport={passport} onClose={() => setPassport(null)} />}
    </div>
  )
}
