import { useEffect, useState, useCallback } from 'react'
import { m3Api } from '../../api/m3'
import { useAuthStore } from '../../stores/authStore'

const statusColors: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  SUBMITTED: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400',
  UNDER_REVIEW: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400',
  APPROVED: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400',
  REJECTED: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400',
}

export function ReportsView() {
  const user = useAuthStore((s) => s.user)
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await m3Api.reports()
      setReports(Array.isArray(data) ? data : [])
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Reports</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Create, review, and manage investigation reports</p>
          </div>
          {user?.role !== 'SUPERVISOR' && (
            <button
              onClick={async () => {
                try {
                  await m3Api.createReport({ title: 'New Investigation Report', status: 'DRAFT' })
                  void load()
                } catch { /* noop */ }
              }}
              className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 transition-colors"
            >
              + New Report
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
            {error}
          </div>
        )}

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
          </div>
        ) : reports.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-10 text-center dark:border-slate-700 dark:bg-slate-800/50">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-700">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400">No reports yet</p>
            <p className="mt-1 text-xs text-slate-400">Generate a case dossier from the AI Chat to create your first report</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-800">
            {reports.map((r: any) => (
              <div key={r.id} className="flex items-center justify-between px-4 py-4 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                <div className="min-w-0">
                  <p className="font-medium text-slate-800 dark:text-slate-200">{r.title || 'Untitled Report'}</p>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                    {r.author ? ` · ${r.author}` : ''}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${statusColors[r.status] || statusColors.DRAFT}`}>
                    {(r.status || 'DRAFT').replace(/_/g, ' ')}
                  </span>
                  <button
                    onClick={async () => {
                      try {
                        await m3Api.reportPdf(r.id)
                      } catch (err) {
                        alert((err as Error).message || 'Unable to download report PDF.')
                      }
                    }}
                    className="flex items-center gap-1 rounded-lg border border-teal-200 bg-teal-50 px-3 py-1.5 text-xs font-semibold text-teal-700 hover:bg-teal-100 dark:border-teal-800 dark:bg-teal-900/30 dark:text-teal-300 transition-colors"
                  >
                    <span className="material-icons-outlined" style={{ fontSize: 14 }}>picture_as_pdf</span>
                    Download PDF
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
