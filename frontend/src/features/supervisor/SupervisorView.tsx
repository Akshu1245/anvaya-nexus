import { useEffect, useState, useCallback } from 'react'
import { m3Api } from '../../api/m3'
import { AuditTrail, ReviewTimeline } from '../../components/SupervisorWorkspace'

type Tab = 'reports' | 'audit' | 'timeline'

export function SupervisorView() {
  const [tab, setTab] = useState<Tab>('reports')
  const [reports, setReports] = useState<any[]>([])
  const [auditEvents, setAuditEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [actionMsg, setActionMsg] = useState('')

  const load = useCallback(async (t: Tab) => {
    setLoading(true); setActionMsg('')
    try {
      if (t === 'reports') {
        const data = await m3Api.reports()
        setReports(Array.isArray(data) ? data : [])
      } else if (t === 'audit') {
        const data = await m3Api.audit('limit=50')
        setAuditEvents(Array.isArray(data) ? data : data?.events || [])
      }
    } catch { /* noop */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void load(tab) }, [tab])

  const handleReview = async (reportId: string, decision: 'APPROVED' | 'REJECTED') => {
    try {
      await m3Api.reviewReport(reportId, { decision, comments: `Supervisor ${decision.toLowerCase()} via Nexus` })
      setActionMsg(`Report ${decision.toLowerCase()} successfully.`)
      void load('reports')
    } catch (e) {
      setActionMsg((e as Error).message)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Supervisor Panel</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Review investigations, approve reports, and monitor platform activity
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-800">
          {([
            { id: 'reports' as Tab, label: 'Reports Queue' },
            { id: 'audit' as Tab, label: 'Audit Trail' },
            { id: 'timeline' as Tab, label: 'Timeline' },
          ] as { id: Tab; label: string }[]).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                tab === t.id
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
                  : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {actionMsg && (
          <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800 dark:border-teal-800 dark:bg-teal-900/20 dark:text-teal-300">
            {actionMsg}
          </div>
        )}

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
          </div>
        ) : (
          <>
            {/* Reports Queue */}
            {tab === 'reports' && (
              reports.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center dark:border-slate-700 dark:bg-slate-800/50">
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">No reports pending review</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-800">
                  {reports.map((r: any) => (
                    <div key={r.id} className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <p className="font-medium text-slate-800 dark:text-slate-200">{r.title || 'Untitled Report'}</p>
                        <p className="mt-0.5 text-xs text-slate-400">
                          {r.author || 'Unknown author'} · {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                        </p>
                        <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          r.status === 'SUBMITTED' ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' :
                          r.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400' :
                          'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                        }`}>
                          {(r.status || 'DRAFT').replace(/_/g, ' ')}
                        </span>
                      </div>
                      {r.status === 'SUBMITTED' && (
                        <div className="flex shrink-0 gap-2">
                          <button
                            onClick={() => handleReview(r.id, 'APPROVED')}
                            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReview(r.id, 'REJECTED')}
                            className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400 transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}

            {/* Audit Trail */}
            {tab === 'audit' && <AuditTrail events={auditEvents} />}

            {/* Timeline */}
            {tab === 'timeline' && <ReviewTimeline timeline={null} />}
          </>
        )}
      </div>
    </div>
  )
}
