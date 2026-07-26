import { useLocation, useNavigate } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import { m3Api } from '../api/m3'

const pageTitles: Record<string, string> = {
  '/app': 'AI Investigation Chat',
  '/app/dashboard': 'Dashboard',
  '/app/analytics': 'Crime Analytics',
  '/app/reports': 'Investigation Reports',
  '/app/workspace': 'Case Workspace',
  '/app/evidence': 'Evidence Repository',
  '/app/supervisor': 'Supervisor Panel',
  '/app/settings': 'Settings',
}

const pageIcons: Record<string, string> = {
  '/app': 'chat',
  '/app/dashboard': 'dashboard',
  '/app/analytics': 'bar_chart',
  '/app/reports': 'description',
  '/app/workspace': 'work',
  '/app/evidence': 'inventory_2',
  '/app/supervisor': 'supervisor_account',
  '/app/settings': 'settings',
}

export function TopBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const conversationTitle = useChatStore((s) => s.conversationTitle)
  const messages = useChatStore((s) => s.messages)
  const { setMobileSidebarOpen, setCommandPaletteOpen, intelligenceOpen, setIntelligenceOpen } = useUIStore()

  const isAIHome = location.pathname === '/app' || location.pathname.startsWith('/app/chat')
  const title = isAIHome
    ? (messages.length > 0 ? conversationTitle : 'AI Investigation Chat')
    : (pageTitles[location.pathname] || 'ANVAYA')
  const pageIcon = isAIHome ? 'chat' : (pageIcons[location.pathname] || 'article')

  const userInitial = (user?.username || 'O').charAt(0).toUpperCase()
  const roleLabel = user?.role?.replace(/_/g, ' ') || ''

  const handleLogout = async () => {
    await m3Api.logout().catch(() => {})
    setUser(null)
    navigate('/auth/login', { replace: true })
  }

  return (
    <header className="flex shrink-0 flex-col" role="banner"
      style={{ borderBottom: '2px solid #c8a84b', background: 'linear-gradient(180deg, #003087 0%, #00246b 100%)', fontFamily: "'Inter', sans-serif" }}>

      {/* Main row */}
      <div className="flex h-12 items-center justify-between px-4" style={{ borderBottom: '1px solid rgba(200,168,75,0.2)' }}>

        {/* Left: mobile burger + real KSP logo + page title */}
        <div className="flex items-center gap-3 min-w-0">
          <button onClick={() => setMobileSidebarOpen(true)}
            className="rounded-lg p-1.5 lg:hidden transition-colors" style={{ color: '#93b8e8' }}
            aria-label="Open sidebar">
            <span className="material-icons-outlined" style={{ fontSize: 22 }}>menu</span>
          </button>

          {/* Real KSP logo — hidden on small screens, shown on lg */}
          <img src="/ksp_logo_real.png" alt="Karnataka State Police"
            className="h-8 w-8 object-contain rounded-full hidden lg:block shrink-0"
            style={{ background: '#fff', border: '1.5px solid #c8a84b' }} />

          <div className="hidden md:block min-w-0">
            <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: '#c8a84b' }}>
              Karnataka State Police
            </p>
            <div className="flex items-center gap-1.5">
              <span className="material-icons-outlined" style={{ fontSize: 13, color: '#93b8e8' }}>{pageIcon}</span>
              <h1 className="text-sm font-semibold text-white truncate" style={{ maxWidth: 280 }}>{title}</h1>
            </div>
          </div>
          <h1 className="text-sm font-semibold text-white truncate md:hidden">{title}</h1>
        </div>

        {/* Right: actions */}
        <div className="flex shrink-0 items-center gap-2">
          {/* Search button */}
          <button onClick={() => setCommandPaletteOpen(true)}
            className="hidden items-center gap-2 rounded-lg px-3 py-1.5 text-xs sm:flex transition-colors"
            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(200,168,75,0.2)', color: '#93b8e8' }}
            aria-label="Search">
            <span className="material-icons-outlined" style={{ fontSize: 14 }}>search</span>
            <span>Search...</span>
            <kbd className="rounded px-1.5 py-0.5 text-[10px]" style={{ background: 'rgba(200,168,75,0.15)', color: '#c8a84b' }}>⌘K</kbd>
          </button>

          {/* Intelligence panel toggle */}
          {isAIHome && messages.length > 0 && (
            <button onClick={() => setIntelligenceOpen(!intelligenceOpen)}
              className="hidden items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium sm:flex transition-colors"
              style={{
                border: intelligenceOpen ? '1px solid #c8a84b' : '1px solid rgba(200,168,75,0.2)',
                background: intelligenceOpen ? 'rgba(200,168,75,0.15)' : 'transparent',
                color: intelligenceOpen ? '#c8a84b' : '#93b8e8',
              }}
              aria-label="Toggle Intelligence Panel">
              <span className="material-icons-outlined" style={{ fontSize: 14 }}>shield</span>
              Intel
            </button>
          )}

          {/* Mobile search */}
          <button onClick={() => setCommandPaletteOpen(true)}
            className="rounded-lg p-1.5 sm:hidden" style={{ color: '#93b8e8' }} aria-label="Search">
            <span className="material-icons-outlined" style={{ fontSize: 20 }}>search</span>
          </button>

          {/* User */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="hidden sm:block text-right">
                <p className="text-[10px] font-semibold" style={{ color: '#c8a84b' }}>{user.username}</p>
                <p className="text-[9px]" style={{ color: '#4a6080' }}>{roleLabel}</p>
              </div>
              <button onClick={() => navigate('/app/settings')}
                className="flex h-8 w-8 items-center justify-center rounded-full font-bold text-xs transition-all"
                style={{ background: '#c8a84b', color: '#003087', boxShadow: '0 2px 8px rgba(200,168,75,0.4)' }}
                title={`${user.username} · ${roleLabel}`}>
                {userInitial}
              </button>
              <button onClick={() => void handleLogout()}
                className="hidden sm:flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors"
                style={{ border: '1px solid rgba(200,168,75,0.2)', color: '#93b8e8', background: 'rgba(255,255,255,0.05)' }}>
                <span className="material-icons-outlined" style={{ fontSize: 14 }}>logout</span>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Breadcrumb strip */}
      <div className="px-4 py-1 flex items-center gap-1.5" style={{ background: 'rgba(0,0,0,0.15)' }}>
        <span className="material-icons-outlined" style={{ fontSize: 12, color: '#4a6080' }}>home</span>
        <span className="text-[10px]" style={{ color: '#4a6080' }}>KSP Portal</span>
        <span className="material-icons-outlined" style={{ fontSize: 12, color: '#2a4060' }}>chevron_right</span>
        <span className="text-[10px]" style={{ color: '#c8a84b' }}>{title}</span>
      </div>
    </header>
  )
}
