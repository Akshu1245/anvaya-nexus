import { useEffect, useState } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useInvestigationStore } from '../../stores/investigationStore'
import { m3Api } from '../../api/m3'

export function DashboardOverview() {
  const user = useAuthStore((s) => s.user)
  const invStore = useInvestigationStore()
  const [sources, setSources] = useState<any[]>([])
  const [homeData, setHomeData] = useState<any>(null)

  useEffect(() => {
    m3Api.sources().then(setSources).catch(() => {})
    m3Api.home().then(setHomeData).catch(() => {})
  }, [])

  const results = invStore.results || []

  return (
    <div className="mx-auto max-w-4xl px-4 pb-4">
      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Dashboard Overview</span>
        <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-navy-900">
          <p className="text-[10px] font-medium text-slate-500 dark:text-slate-400">Active Cases</p>
          <p className="mt-0.5 text-lg font-bold text-teal-700 dark:text-teal-400">{results.length || '—'}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-navy-900">
          <p className="text-[10px] font-medium text-slate-500 dark:text-slate-400">Investigations</p>
          <p className="mt-0.5 text-lg font-bold text-purple-700 dark:text-purple-400">{homeData?.recent_investigations?.length || 0}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-navy-900">
          <p className="text-[10px] font-medium text-slate-500 dark:text-slate-400">Sources</p>
          <p className="mt-0.5 text-lg font-bold text-emerald-700 dark:text-emerald-400">{sources.filter((s: any) => s.status === 'Fresh').length}/{sources.length}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-navy-900">
          <p className="text-[10px] font-medium text-slate-500 dark:text-slate-400">Role</p>
          <p className="mt-0.5 text-lg font-bold text-amber-700 dark:text-amber-400">{user?.role?.replace(/_/g, ' ') || '—'}</p>
        </div>
      </div>

      {homeData?.degraded_mode && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
          ⚠ Degraded mode: {homeData.degraded_sources?.join(', ')} unavailable
        </div>
      )}
    </div>
  )
}
