import { SupervisorDashboard } from '../components/SupervisorDashboard'
import { useAuthStore } from '../stores/authStore'

export function SupervisorPage() {
  const user = useAuthStore((s) => s.user)

  if (user?.role !== 'SUPERVISOR') {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-bold text-navy-950">Supervisor Workspace</h1>
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          This area is restricted to supervisor accounts.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-950">Supervisor Workspace</h1>
        <p className="mt-1 text-sm text-slate-500">Review investigations and audit trails</p>
      </div>
      <SupervisorDashboard />
    </div>
  )
}
