import { useAuthStore } from '../../stores/authStore'
import { m3Api } from '../../api/m3'

export function SettingsView() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)

  const handleLogout = async () => {
    await m3Api.logout().catch(() => {})
    setUser(null)
    window.location.href = '/auth/login'
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-lg font-bold text-slate-900">Settings</h2>
      <div className="mt-6 space-y-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700">Account</h3>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            <p><span className="font-medium">Username:</span> {user?.username}</p>
            <p><span className="font-medium">Role:</span> {user?.role}</p>
            <p><span className="font-medium">Station:</span> {user?.assigned_station || '—'}</p>
            <p><span className="font-medium">District:</span> {user?.assigned_district || '—'}</p>
          </div>
          <button onClick={handleLogout} className="mt-4 rounded-lg border border-red-200 px-4 py-2 text-xs font-medium text-red-700 hover:bg-red-50">
            Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}
