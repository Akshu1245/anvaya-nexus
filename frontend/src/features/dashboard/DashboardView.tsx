import { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { m3Api } from '../../api/m3'
import { Link } from 'react-router-dom'
import { useLocale } from '../../i18n/portal'

function StatCard({ label, value, sub, icon, color, bg }: {
  label: string; value: string | number; sub?: string; icon: string; color: string; bg: string
}) {
  return (
    <div className="rounded-xl bg-white p-5 shadow-sm transition-all dark:bg-slate-800 dark:border-slate-700"
      style={{ border: '1px solid #e2e8f0' }}
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,48,135,0.1)')}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '')}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-bold" style={{ color }}>{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        <div className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ background: bg }}>
          <span className="material-icons-outlined" style={{ fontSize: 22, color }}>{icon}</span>
        </div>
      </div>
    </div>
  )
}

export function DashboardView() {
  const user = useAuthStore((s) => s.user)
  const { t } = useLocale()
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await m3Api.dashboardStats()
      setStats(data)
    } catch (e) {
      setError((e as Error).message || 'Unable to load dashboard data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const recentCases = stats?.recent_cases || []
  const byOffence = stats?.by_offence || []
  const displayName = user?.username?.split('/')?.[0] || user?.username || 'Officer'

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6" style={{ fontFamily: "'Inter', sans-serif" }}>
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span className="material-icons-outlined" style={{ color: '#003087', fontSize: 24 }}>dashboard</span>
              {t('dash.title')}
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {t('dash.subtitle')}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              Welcome back, <span className="font-semibold text-blue-700 dark:text-blue-400">{displayName}</span>
              {user?.assigned_station ? ` · ${user.assigned_station}` : ''}
            </p>
          </div>
          <button onClick={() => void load()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{ border: '1px solid #e2e8f0', color: '#64748b' }}
            title="Refresh">
            <span className="material-icons-outlined" style={{ fontSize: 16 }}>refresh</span>
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg px-4 py-3 text-sm flex items-center gap-2"
            style={{ background: '#fff7ed', border: '1px solid #fed7aa', color: '#92400e' }}>
            <span className="material-icons-outlined" style={{ fontSize: 16 }}>warning_amber</span>
            {error} — Displaying cached data if available.
          </div>
        )}

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 rounded-xl animate-pulse" style={{ background: '#f1f5f9' }} />
            ))}
          </div>
        ) : (
          <>
            {/* Stats */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label={t('dash.totalFirs')} value={stats?.total_firs ?? '—'} sub="in database" icon="folder_open" color="#003087" bg="#eff4ff" />
              <StatCard label={t('dash.pendingCases')} value={stats?.pending ?? '—'} sub="awaiting resolution" icon="pending" color="#d97706" bg="#fffbeb" />
              <StatCard label={t('dash.resolvedCases')} value={stats?.resolved ?? '—'} sub="closed / charge-sheeted" icon="check_circle" color="#059669" bg="#ecfdf5" />
              <StatCard label={t('dash.priorityAlerts')} value={stats?.priority ?? '—'} sub="high / critical severity" icon="priority_high" color="#dc2626" bg="#fef2f2" />
            </div>

            {/* Quick actions */}
            <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'AI Chat', icon: 'chat', to: '/app', color: '#003087', bg: '#eff4ff' },
                { label: 'Analytics', icon: 'bar_chart', to: '/app/analytics', color: '#7c3aed', bg: '#f5f3ff' },
                { label: 'Reports', icon: 'description', to: '/app/reports', color: '#059669', bg: '#ecfdf5' },
                { label: 'Evidence', icon: 'inventory_2', to: '/app/evidence', color: '#d97706', bg: '#fffbeb' },
              ].map((a) => (
                <Link key={a.label} to={a.to}
                  className="rounded-xl p-4 bg-white flex items-center gap-3 transition-all"
                  style={{ border: '1px solid #e2e8f0' }}
                  onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'; e.currentTarget.style.borderColor = a.color }}
                  onMouseLeave={(e) => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.borderColor = '#e2e8f0' }}>
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: a.bg }}>
                    <span className="material-icons-outlined" style={{ fontSize: 20, color: a.color }}>{a.icon}</span>
                  </div>
                  <span className="text-sm font-semibold text-slate-700">{a.label}</span>
                </Link>
              ))}
            </div>

            {/* Recent cases + Offence breakdown */}
            <div className="mt-6 grid gap-6 lg:grid-cols-5">
              {/* Recent cases */}
              <div className="lg:col-span-3">
                <h3 className="mb-3 text-sm font-bold text-slate-700 flex items-center gap-1.5">
                  <span className="material-icons-outlined" style={{ fontSize: 16, color: '#003087' }}>history</span>
                  Recent Cases
                </h3>
                {recentCases.length > 0 ? (
                  <div className="rounded-xl overflow-hidden bg-white" style={{ border: '1px solid #e2e8f0' }}>
                    {recentCases.map((c: any, i: number) => (
                      <div key={c.id || i} className="flex items-center justify-between px-4 py-3 text-sm border-b last:border-b-0"
                        style={{ borderColor: '#f1f5f9' }}>
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-800 truncate" style={{ fontSize: 13 }}>
                            {c.crime_number || c.fir_number || c.id}
                          </p>
                          <p className="text-xs text-slate-400 truncate">{c.offence_type} · {c.unit_name}</p>
                        </div>
                        <span className={`shrink-0 ml-2 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                          (c.status || '').toLowerCase().includes('pending') || (c.status || '').toLowerCase().includes('unresolv')
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-emerald-50 text-emerald-700'
                        }`}>
                          {c.status || 'Pending'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl bg-slate-50 p-8 text-center" style={{ border: '1px dashed #d0d9e8' }}>
                    <span className="material-icons-outlined text-3xl text-slate-300">folder_open</span>
                    <p className="mt-2 text-sm text-slate-500">No case data available</p>
                    <Link to="/app" className="mt-2 inline-flex items-center gap-1 text-xs font-medium" style={{ color: '#003087' }}>
                      <span className="material-icons-outlined" style={{ fontSize: 14 }}>chat</span>
                      Start AI Investigation
                    </Link>
                  </div>
                )}
              </div>

              {/* Offence breakdown */}
              <div className="lg:col-span-2">
                <h3 className="mb-3 text-sm font-bold text-slate-700 flex items-center gap-1.5">
                  <span className="material-icons-outlined" style={{ fontSize: 16, color: '#003087' }}>donut_small</span>
                  Top Offence Types
                </h3>
                {byOffence.length > 0 ? (
                  <div className="rounded-xl bg-white p-4 space-y-2" style={{ border: '1px solid #e2e8f0' }}>
                    {byOffence.map((o: any, i: number) => {
                      const pct = stats?.total_firs ? Math.round((o.count / stats.total_firs) * 100) : 0
                      return (
                        <div key={i}>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-slate-700 font-medium truncate" style={{ maxWidth: 140 }}>{o.offence}</span>
                            <span className="text-slate-500 shrink-0 ml-1">{o.count} ({pct}%)</span>
                          </div>
                          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#f1f5f9' }}>
                            <div className="h-full rounded-full transition-all"
                              style={{ width: `${pct}%`, background: '#003087', opacity: 1 - i * 0.12 }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="rounded-xl bg-slate-50 p-6 text-center" style={{ border: '1px dashed #d0d9e8' }}>
                    <span className="material-icons-outlined text-2xl text-slate-300">bar_chart</span>
                    <p className="mt-1 text-xs text-slate-500">No offence data</p>
                  </div>
                )}
              </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-6 rounded-xl px-4 py-3 flex items-start gap-2"
              style={{ background: '#fff7ed', border: '1px solid #fed7aa' }}>
              <span className="material-icons-outlined shrink-0 text-amber-600" style={{ fontSize: 15 }}>warning_amber</span>
              <p className="text-xs text-amber-700">
                <strong>Synthetic Data:</strong> All metrics are from the KSP Datathon 2026 prototype database.
                No real FIR or operational data is used.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
