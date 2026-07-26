import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const role = user?.role ?? 'INVESTIGATOR'

  const summaries = [
    { label: 'Active Investigations', value: '—', color: 'bg-teal-50 text-teal-700' },
    { label: 'Open Tasks', value: '—', color: 'bg-blue-50 text-blue-700' },
    { label: 'Pending Reviews', value: role === 'SUPERVISOR' ? '—' : '—', color: 'bg-amber-50 text-amber-700' },
    { label: 'System Status', value: 'Online', color: 'bg-emerald-50 text-emerald-700' },
  ]

  const quickActions = [
    { label: 'New Search', path: '/dashboard/search', description: 'Query across FIR records' },
    { label: 'Open Workspace', path: '/dashboard/workspace', description: 'Investigation chat & tools' },
    { label: 'View Analytics', path: '/dashboard/analytics', description: 'Briefings & crime trends' },
    { label: 'Generate Report', path: '/dashboard/reports', description: 'Build cited dossier' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-950">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Welcome{user ? `, ${user.username}` : ''}. Role: {role.replace(/_/g, ' ').toLowerCase()}.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaries.map((item) => (
          <div key={item.label} className={`rounded-xl border p-4 ${item.color}`}>
            <p className="text-xs font-medium opacity-75">{item.label}</p>
            <p className="mt-1 text-2xl font-bold">{item.value}</p>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-sm font-semibold text-navy-950">Quick Actions</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.path}
              to={action.path}
              className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-teal-300 hover:shadow-sm"
            >
              <p className="font-medium text-navy-950">{action.label}</p>
              <p className="mt-1 text-xs text-slate-500">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-sm font-semibold text-navy-950">Recent Activity</h2>
        <p className="mt-2 text-sm text-slate-400">No recent activity yet. Start a new search or open the workspace.</p>
      </div>
    </div>
  )
}
