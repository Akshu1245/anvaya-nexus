import { useState, useEffect } from 'react'
import { m3Api } from '../api/m3'
import { AuditTrail } from './SupervisorWorkspace'

export function SupervisorDashboard({ onOpenReport, onRefresh }: { onOpenReport?: (id: string) => void; onRefresh?: () => void }) {
  const [reports, setReports] = useState<any[]>([])
  const [events, setEvents] = useState<any[]>([])
  const [health, setHealth] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'queue' | 'audit' | 'health'>('queue')
  const [busy, setBusy] = useState('')

  const act = async (label: string, fn: () => Promise<any>) => {
    setBusy(label)
    try { return await fn() }
    catch { return null }
    finally { setBusy('') }
  }

  useEffect(() => {
    void act('load', async () => {
      const r = await m3Api.reports().catch(() => null)
      if (r) setReports(r.reports || [])
    })
  }, [])

  const loadAudit = async () => {
    const data = await act('audit', () => m3Api.audit('limit=15'))
    if (data) setEvents(data.events || [])
  }

  const loadHealth = async () => {
    const data = await act('health', m3Api.systemHealth)
    if (data) setHealth(data)
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-1 border-b border-slate-100 px-3 py-2">
        {(['queue', 'audit', 'health'] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => { setActiveTab(tab); if (tab === 'audit') loadAudit(); if (tab === 'health') loadHealth() }}
            className={`rounded-md px-2 py-1 text-[11px] font-semibold transition-colors ${
              activeTab === tab ? 'bg-navy-900 text-white' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
            }`}
          >
            {tab === 'queue' ? 'Review Queue' : tab === 'audit' ? 'Audit' : 'Health'}
          </button>
        ))}
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="ml-auto rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            title="Refresh"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'queue' && (
          <div className="space-y-2 p-3">
            <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Assigned for Review</h4>
            {reports.length === 0 && (
              <p className="py-8 text-center text-xs text-slate-400">No reports assigned for review.</p>
            )}
            {reports.map((r: any) => (
              <div key={r.id} className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-800 line-clamp-1">{r.title}</p>
                    <p className="mt-0.5 text-slate-500">{r.id}</p>
                  </div>
                  <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${
                    r.status === 'SUBMITTED' ? 'bg-blue-50 text-blue-700' :
                    r.status === 'CHANGES_REQUESTED' ? 'bg-amber-50 text-amber-700' :
                    r.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700' :
                    r.status === 'REJECTED' ? 'bg-red-50 text-red-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {r.status || 'draft'}
                  </span>
                </div>
                {(r.status === 'SUBMITTED' || r.status === 'CHANGES_REQUESTED') && (
                  <button
                    type="button"
                    onClick={() => onOpenReport?.(r.id)}
                    className="mt-2 rounded bg-navy-800 px-3 py-1 text-[10px] font-medium text-white hover:bg-navy-700"
                  >
                    Review
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'audit' && (
          <AuditTrail events={events} />
        )}

        {activeTab === 'health' && (
          <div className="space-y-3 p-3">
            <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">System Health</h4>
            {!health && busy !== 'health' && (
              <p className="py-8 text-center text-xs text-slate-400">Click Health tab to check.</p>
            )}
            {health && (
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${health.backend === 'ok' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="font-medium text-slate-700">Backend: {health.backend || health.status}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${health.database === 'ok' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="font-medium text-slate-700">Database: {health.database}</span>
                </div>
                {health.degraded_mode && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-amber-800">
                    Degraded mode — {health.degraded_reasons?.join(', ') || 'some sources unavailable'}
                  </div>
                )}
                {health.sources?.map((s: any) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border border-slate-100 bg-white p-2">
                    <span className="text-slate-700">{s.name || s.id}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${
                      s.status === 'Fresh' ? 'bg-emerald-50 text-emerald-700' :
                      s.status === 'Unavailable' ? 'bg-red-50 text-red-700' :
                      'bg-amber-50 text-amber-700'
                    }`}>
                      {s.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {busy && (
        <div className="border-t border-slate-100 p-2 text-center text-[10px] text-slate-400">
          {busy}...
        </div>
      )}
    </div>
  )
}
