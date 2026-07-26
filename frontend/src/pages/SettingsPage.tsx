import { useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useLocale } from '../i18n/portal'

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const { locale, setLocale } = useLocale()
  const [tab, setTab] = useState<'profile' | 'preferences'>('profile')

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-950">Settings</h1>
      </div>

      <div className="flex gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1">
        <button type="button" onClick={() => setTab('profile')} className={`rounded-md px-4 py-2 text-sm font-medium transition ${tab === 'profile' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>Profile</button>
        <button type="button" onClick={() => setTab('preferences')} className={`rounded-md px-4 py-2 text-sm font-medium transition ${tab === 'preferences' ? 'bg-white text-navy-950 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>Preferences</button>
      </div>

      {tab === 'profile' && (
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          <div>
            <p className="text-xs font-medium text-slate-500">Username</p>
            <p className="text-sm font-medium text-navy-950">{user?.username || '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Role</p>
            <p className="text-sm font-medium text-navy-950">{user?.role?.replace(/_/g, ' ') || '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Station</p>
            <p className="text-sm font-medium text-navy-950">{user?.assigned_station || '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">District</p>
            <p className="text-sm font-medium text-navy-950">{user?.assigned_district || '—'}</p>
          </div>
        </div>
      )}

      {tab === 'preferences' && (
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          <div>
            <p className="text-sm font-medium text-navy-950">Language</p>
            <div className="mt-2 flex gap-2">
              <button type="button" aria-pressed={locale === 'en'} onClick={() => setLocale('en')} className={`rounded-lg border px-4 py-2 text-sm font-medium ${locale === 'en' ? 'border-teal-400 bg-teal-50 text-teal-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>English</button>
              <button type="button" aria-pressed={locale === 'kn'} onClick={() => setLocale('kn')} className={`rounded-lg border px-4 py-2 text-sm font-medium ${locale === 'kn' ? 'border-teal-400 bg-teal-50 text-teal-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>ಕನ್ನಡ</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
