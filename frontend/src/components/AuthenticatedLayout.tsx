import { type ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useLocale, LocaleProvider } from '../i18n/portal'
import { m3Api } from '../api/m3'

const navItems = [
  { label: 'Dashboard', labelKn: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್', path: '/dashboard', icon: '▦' },
  { label: 'Search', labelKn: 'ಹುಡುಕಾಟ', path: '/dashboard/search', icon: '○' },
  { label: 'Workspace', labelKn: 'ಕಾರ್ಯಕ್ಷೇತ್ರ', path: '/dashboard/workspace', icon: '◈' },
  { label: 'Analytics', labelKn: 'ವಿಶ್ಲೇಷಣೆ', path: '/dashboard/analytics', icon: '◉' },
  { label: 'Reports', labelKn: 'ವರದಿಗಳು', path: '/dashboard/reports', icon: '▣' },
  { label: 'Health', labelKn: 'ಆರೋಗ್ಯ', path: '/dashboard/health', icon: '●' },
]

export function AuthenticatedLayout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { t, locale, setLocale } = useLocale()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = async () => {
    await m3Api.logout().catch(() => {})
    setUser(null)
  }

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="flex min-h-screen" style={{ background: '#f5f5f0' }}>
      {/* ── Sidebar ── */}
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-60 flex-col transition-all ${sidebarOpen ? 'translate-x-0' : '-translate-x-60'}`}
        style={{ background: '#0d1f3c', borderRight: '2px solid rgba(200,168,75,0.3)' }}>

        {/* Sidebar header */}
        <div className="flex items-center gap-3 px-4 py-4" style={{ borderBottom: '1px solid rgba(200,168,75,0.2)', background: 'rgba(0,0,0,0.2)' }}>
          <img src="/ksp_logo_real.png" alt="KSP" className="h-10 w-10 object-contain rounded-full shrink-0"
            style={{ border: '1px solid #c8a84b', background: '#fff' }} />
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: '#c8a84b' }}>Karnataka Police</p>
            <p className="text-sm font-bold text-white">ANVAYA NEXUS</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 p-3" aria-label="Primary navigation">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
              style={isActive(item.path) ? {
                background: 'rgba(200,168,75,0.15)',
                color: '#c8a84b',
                border: '1px solid rgba(200,168,75,0.3)',
              } : {
                color: '#93b8e8',
                border: '1px solid transparent',
              }}
            >
              <span className="w-5 text-center text-xs" aria-hidden style={{ color: isActive(item.path) ? '#c8a84b' : '#4a6a90' }}>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Settings link */}
        <div className="p-3" style={{ borderTop: '1px solid rgba(200,168,75,0.2)' }}>
          <Link
            to="/dashboard/settings"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
            style={{ color: '#93b8e8' }}
          >
            <span className="w-5 text-center text-xs" aria-hidden style={{ color: '#4a6a90' }}>⚙</span>
            Settings
          </Link>
          {user && (
            <div className="mt-2 flex items-center gap-2 rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(200,168,75,0.15)' }}>
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold" style={{ background: 'linear-gradient(135deg, #c8a84b, #e8c96b)', color: '#0d1f3c' }}>
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-white truncate">{user.username}</p>
                <p className="text-[10px]" style={{ color: '#4a6a90' }}>{user.role?.replace(/_/g, ' ')}</p>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main content ── */}
      <div className={`flex flex-1 flex-col ${sidebarOpen ? 'ml-60' : 'ml-0'}`}>

        {/* Top header */}
        <header className="sticky top-0 z-20 flex flex-col shrink-0" style={{ borderBottom: '2px solid #c8a84b', background: 'linear-gradient(180deg, #0d1f3c 0%, #152840 100%)' }}>
          {/* Main top row */}
          <div className="flex h-12 items-center justify-between px-4" style={{ borderBottom: '1px solid rgba(200,168,75,0.2)' }}>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-lg p-1.5 transition-colors"
                style={{ color: '#93b8e8' }}
                aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
              </button>
              <img src="/ksp_logo_real.png" alt="KSP" className="h-7 w-7 object-contain rounded-full hidden md:block"
                style={{ border: '1px solid #c8a84b', background: '#fff' }} />
              <div className="hidden md:block">
                <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: '#c8a84b' }}>Karnataka State Police</p>
                <p className="text-xs font-semibold text-white">
                  {location.pathname === '/dashboard' ? 'Dashboard' : location.pathname.split('/').pop()?.replace(/-/g, ' ').replace(/^\w/, (c) => c.toUpperCase())}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Language toggle */}
              <div className="flex items-center gap-1 rounded-lg p-0.5" style={{ border: '1px solid rgba(200,168,75,0.25)', background: 'rgba(0,0,0,0.2)' }}>
                <button
                  type="button"
                  aria-pressed={locale === 'kn'}
                  onClick={() => setLocale('kn')}
                  className="rounded-md px-2 py-1 text-xs font-medium transition-colors"
                  style={locale === 'kn' ? { background: '#c8a84b', color: '#0d1f3c' } : { color: '#93b8e8' }}
                >ಕನ್ನಡ</button>
                <button
                  type="button"
                  aria-pressed={locale === 'en'}
                  onClick={() => setLocale('en')}
                  className="rounded-md px-2 py-1 text-xs font-medium transition-colors"
                  style={locale === 'en' ? { background: '#c8a84b', color: '#0d1f3c' } : { color: '#93b8e8' }}
                >EN</button>
              </div>

              {user && (
                <div className="flex items-center gap-2">
                  <span className="text-xs hidden sm:block" style={{ color: '#93b8e8' }}>{user.username}</span>
                  <button
                    type="button"
                    onClick={() => void handleLogout()}
                    className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
                    style={{ border: '1px solid rgba(200,168,75,0.25)', color: '#c8a84b', background: 'rgba(200,168,75,0.05)' }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Breadcrumb */}
          <div className="px-4 py-1 flex items-center gap-2" style={{ background: 'rgba(0,0,0,0.15)' }}>
            <span className="text-[10px]" style={{ color: '#4a6080' }}>KSP Portal</span>
            <span className="text-[10px]" style={{ color: '#2a4060' }}>›</span>
            <span className="text-[10px]" style={{ color: '#c8a84b' }}>
              {location.pathname === '/dashboard' ? 'Dashboard' : location.pathname.split('/').pop()?.replace(/-/g, ' ').replace(/^\w/, (c) => c.toUpperCase())}
            </span>
          </div>
        </header>

        <main className="flex-1 p-6">
          {children}
        </main>

        <footer style={{ borderTop: '2px solid rgba(200,168,75,0.2)', background: '#0d1f3c' }}>
          <div className="flex h-1 w-full">
            <div className="flex-1" style={{ background: '#FF9933' }} />
            <div className="flex-1 bg-white" />
            <div className="flex-1" style={{ background: '#138808' }} />
          </div>
          <div className="px-6 py-3 flex items-center gap-3">
            <img src="/ksp_logo_real.png" alt="KSP" className="h-6 w-6 object-contain rounded-full" style={{ border: '1px solid rgba(200,168,75,0.4)' }} />
            <p className="text-xs" style={{ color: '#4a6080' }}>
              © 2026 Karnataka State Police · KSP Datathon Prototype · Synthetic Data Only · No live CCTNS connection
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
