import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { m3Api } from '../api/m3'
import { btnPrimary } from '../components/PortalButtons'
import { useLocale } from '../i18n/portal'
import { useAuthStore } from '../stores/authStore'
import { ShiftBriefingPanel, CrimeTrendsPanel } from '../features/m4/InvestigationExperience'

export function AnalyticsPage() {
  const { locale, t } = useLocale()
  const [searchParams] = useSearchParams()
  const user = useAuthStore((s) => s.user)
  const initialTab = searchParams.get('tab') === 'trends' ? 'trends' : 'briefing'
  const [tab, setTab] = useState<'briefing' | 'trends'>(initialTab as any)
  const [briefing, setBriefing] = useState<any>(null)
  const [trends, setTrends] = useState<any>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const call = async (label: string, fn: () => Promise<any>) => { setBusy(label); setError(''); try { return await fn() } catch (e) { setError((e as Error).message); return null } finally { setBusy('') } }

  const isSupervisor = user?.role === 'SUPERVISOR'

  async function loadBriefing() {
    if (isSupervisor) { setError('Supervisor Review does not grant access.'); return }
    const data = await call('briefing', () => m3Api.briefing('default'))
    if (data) setBriefing(data)
  }

  async function loadTrends() {
    if (isSupervisor) { setError('Supervisor Review does not grant access.'); return }
    const data = await call('trends', () => m3Api.trends('default'))
    if (data) setTrends(data)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-950">{locale === 'kn' ? 'ವಿಶ್ಲೇಷಣೆ' : 'Analytics'}</h1>
        <p className="mt-1 text-sm text-slate-500">{locale === 'kn' ? 'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ಮತ್ತು ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು' : 'Shift briefings and crime trends'}</p>
      </div>

      <div className="flex gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1">
        <button type="button" onClick={() => setTab('briefing')} className={`rounded-md px-4 py-2 text-sm font-medium transition ${tab === 'briefing' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>{locale === 'kn' ? 'ಬ್ರೀಫಿಂಗ್' : 'Briefing'}</button>
        <button type="button" onClick={() => setTab('trends')} className={`rounded-md px-4 py-2 text-sm font-medium transition ${tab === 'trends' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>{locale === 'kn' ? 'ಪ್ರವೃತ್ತಿಗಳು' : 'Trends'}</button>
      </div>

      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      {busy && <p role="status" className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-600">{t('loading')} — {busy}</p>}

      {tab === 'briefing' && (
        <div className="space-y-4">
          <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={() => void loadBriefing()}>{busy === 'briefing' ? t('loading') : t('loadBriefing')}</button>
          {briefing ? <ShiftBriefingPanel data={briefing} /> : <div className="rounded-lg border bg-white p-6 text-sm text-slate-500">{locale === 'kn' ? 'ಬ್ರೀಫಿಂಗ್ ಲೋಡ್ ಮಾಡಿ.' : 'Load the shift briefing.'}</div>}
        </div>
      )}

      {tab === 'trends' && (
        <div className="space-y-4">
          <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={() => void loadTrends()}>{busy === 'trends' ? t('loading') : t('loadTrends')}</button>
          {trends ? <CrimeTrendsPanel data={trends} /> : <div className="rounded-lg border bg-white p-6 text-sm text-slate-500">{locale === 'kn' ? 'ಪ್ರವೃತ್ತಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಿ.' : 'Load crime trends.'}</div>}
        </div>
      )}
    </div>
  )
}
