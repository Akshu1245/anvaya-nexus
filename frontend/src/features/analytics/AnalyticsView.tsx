import { useEffect, useState, useCallback } from 'react'
import { m3Api } from '../../api/m3'

export function AnalyticsView() {
  const [briefing, setBriefing] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      // Home data has aggregate stats; no investigation context needed for basic trends
      const data = await m3Api.home()
      setBriefing(data)
    } catch { /* backend may be offline */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void load() }, [load])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Analytics</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Crime trends, shift briefings, and data aggregation</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {/* Crime Trends card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Crime Trends</h3>
              <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-[10px] font-semibold text-teal-700 dark:bg-teal-900/20 dark:text-teal-400">Live</span>
            </div>
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <div key={i} className="skeleton h-4 rounded" />)}
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Open an investigation in AI Chat and ask{' '}
                  <span className="font-mono rounded bg-slate-100 px-1 py-0.5 text-[11px] dark:bg-slate-700">"Show recorded crime trends"</span>
                  {' '}to view detailed trend analysis.
                </p>
                <div className="flex h-32 items-end gap-2">
                  {[40, 65, 45, 78, 52, 88, 60].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-t bg-teal-100 dark:bg-teal-900/40 transition-all hover:bg-teal-200 dark:hover:bg-teal-800/60"
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
                <div className="flex justify-between text-[10px] text-slate-400">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
                    <span key={d}>{d}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Shift Briefing card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Shift Briefing</h3>
              <span className="rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-semibold text-purple-700 dark:bg-purple-900/20 dark:text-purple-400">AI</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Ask <span className="font-mono rounded bg-slate-100 px-1 py-0.5 text-[11px] dark:bg-slate-700">"Show my shift briefing"</span>{' '}
              in AI Chat to get an AI-generated overview of what happened since your last shift.
            </p>
            <div className="mt-4 space-y-2">
              {['Unresolved cases', 'New FIRs filed', 'Priority alerts', 'Network connections'].map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
                  <span className="text-xs text-slate-500 dark:text-slate-400">{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Geo Hotspots */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800 sm:col-span-2">
            <h3 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Data Sources Status</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {['CCTNS Replica', 'Forensics DB', 'Vehicle Registry', 'Context Records'].map((source, i) => (
                <div key={source} className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-center dark:border-slate-700 dark:bg-slate-800/60">
                  <div className={`mx-auto mb-2 h-2 w-2 rounded-full ${i < 3 ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                  <p className="text-[11px] font-medium text-slate-700 dark:text-slate-300">{source}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">{i < 3 ? 'Online' : 'Syncing'}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
