import { useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import { useLocale } from '../i18n/portal'
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

const pageTitlesKn: Record<string, string> = {
  '/app': 'ಎಐ ತನಿಖಾ ಚಾಟ್',
  '/app/dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
  '/app/analytics': 'ಅಪರಾಧ ವಿಶ್ಲೇಷಣೆ',
  '/app/reports': 'ತನಿಖಾ ವರದಿಗಳು',
  '/app/workspace': 'ಕೇಸ್ ಕಾರ್ಯಕ್ಷೇತ್ರ',
  '/app/evidence': 'ಸಾಕ್ಷ್ಯ ಭಂಡಾರ',
  '/app/supervisor': 'ಮೇಲ್ವಿಚಾರಕರ ಫಲಕ',
  '/app/settings': 'ಸಂಯೋಜನೆಗಳು',
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
  const sessions = useChatStore((s) => s.sessions)
  const restoreSession = useChatStore((s) => s.restoreSession)
  const toggleBookmark = useChatStore((s) => s.toggleBookmark)
  const { locale, setLocale, t } = useLocale()
  const { setMobileSidebarOpen, setCommandPaletteOpen, intelligenceOpen, setIntelligenceOpen } = useUIStore()
  const [bookmarksModalOpen, setBookmarksModalOpen] = useState(false)

  // Gather all bookmarked messages across active messages and sessions
  const allBookmarks: Array<{ message: any; sessionTitle: string; sessionId: string }> = []
  
  // From current active messages
  messages.filter((m) => m.bookmarked).forEach((m) => {
    allBookmarks.push({ message: m, sessionTitle: conversationTitle || 'Current Chat', sessionId: '' })
  })

  // From stored sessions
  sessions.forEach((s) => {
    (s.messages || []).filter((m: any) => m.bookmarked).forEach((m: any) => {
      if (!allBookmarks.some((b) => b.message.id === m.id)) {
        allBookmarks.push({ message: m, sessionTitle: s.title || 'Saved Chat', sessionId: s.id })
      }
    })
  })

  const isAIHome = location.pathname === '/app' || location.pathname.startsWith('/app/chat')
  const navKey = location.pathname === '/app/dashboard' ? 'nav.dashboard'
    : location.pathname === '/app/analytics' ? 'nav.analytics'
    : location.pathname === '/app/reports' ? 'nav.reports'
    : location.pathname === '/app/evidence' ? 'nav.evidence'
    : location.pathname === '/app/supervisor' ? 'nav.supervisor'
    : location.pathname === '/app/settings' ? 'nav.settings'
    : 'nav.home'
  const title = isAIHome ? (messages.length > 0 ? conversationTitle : t('nav.home')) : t(navKey)
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
          {/* AI Model & Voice Badges */}
          <div className="hidden lg:flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold"
            style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(200,168,75,0.4)', color: '#fff' }}>
            <span className="flex items-center gap-1 text-[11px] text-amber-300">
              <span className="material-icons-outlined" style={{ fontSize: 13, color: '#60a5fa' }}>auto_awesome</span>
              <span>Gemini 2.5 Flash</span>
            </span>
            <span className="text-slate-400">·</span>
            <span className="flex items-center gap-1 text-[11px] text-teal-300" title="Sarvam Saaras STT, Bulbul TTS, Mayura Translate active">
              <span className="material-icons-outlined" style={{ fontSize: 13, color: '#2dd4bf' }}>record_voice_over</span>
              <span>Sarvam AI Suite</span>
            </span>
          </div>

          {/* Language Switcher (EN / ಕನ್ನಡ) */}
          <button
            onClick={() => setLocale(locale === 'en' ? 'kn' : 'en')}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold transition-all shadow-sm"
            style={{
              background: locale === 'kn' ? '#c8a84b' : 'rgba(255,255,255,0.15)',
              color: locale === 'kn' ? '#003087' : '#ffffff',
              border: '1.5px solid #c8a84b',
            }}
            title="Switch Language (English / ಕನ್ನಡ)"
          >
            <span className="material-icons-outlined" style={{ fontSize: 15 }}>translate</span>
            <span>{locale === 'en' ? '🌐 Language: EN (Click for ಕನ್ನಡ)' : '🇮🇳 ಭಾಷೆ: ಕನ್ನಡ (English)'}</span>
          </button>

          {/* Bookmarked items button */}
          <button
            onClick={() => setBookmarksModalOpen(true)}
            className="relative flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-all"
            style={{
              background: 'rgba(255,255,255,0.08)',
              color: '#c8a84b',
              border: '1px solid rgba(200,168,75,0.3)',
            }}
            title="View Bookmarked Messages"
          >
            <span className="material-icons-outlined" style={{ fontSize: 14 }}>bookmark</span>
            <span className="hidden sm:inline">{locale === 'kn' ? 'ಬುಕ್‌ಮಾರ್ಕ್‌ಗಳು' : 'Bookmarks'}</span>
            {allBookmarks.length > 0 && (
              <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500 px-1 text-[10px] font-bold text-slate-900">
                {allBookmarks.length}
              </span>
            )}
          </button>

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

      {/* Bookmarks Modal */}
      {bookmarksModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
          onClick={() => setBookmarksModalOpen(false)}>
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 animate-scale-in"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b pb-3 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <span className="material-icons-outlined text-amber-500" style={{ fontSize: 22 }}>bookmark</span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {locale === 'kn' ? 'ಬುಕ್‌ಮಾರ್ಕ್ ಮಾಡಿದ ಸಂದೇಶಗಳು' : 'Bookmarked Insights'}
                </h3>
              </div>
              <button onClick={() => setBookmarksModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
                <span className="material-icons-outlined" style={{ fontSize: 18 }}>close</span>
              </button>
            </div>

            <div className="mt-4 max-h-96 overflow-y-auto space-y-3">
              {allBookmarks.length === 0 ? (
                <div className="py-8 text-center">
                  <span className="material-icons-outlined text-3xl text-slate-300 dark:text-slate-600">bookmark_border</span>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    {locale === 'kn' ? 'ಯಾವುದೇ ಬುಕ್‌ಮಾರ್ಕ್‌ಗಳಿಲ್ಲ' : 'No bookmarked messages yet'}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    {locale === 'kn'
                      ? 'ಸಂದೇಶದ ಮೇಲಿನ ಬುಕ್‌ಮಾರ್ಕ್ ಐಕಾನ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಅವುಗಳನ್ನು ಇಲ್ಲಿ ಕಾಣಬಹುದು.'
                      : 'Click the bookmark icon on any message in AI Chat to save it for quick reference.'}
                  </p>
                </div>
              ) : (
                allBookmarks.map(({ message, sessionTitle, sessionId }) => (
                  <div key={message.id} className="rounded-xl border border-slate-200 p-3 bg-slate-50 dark:bg-slate-800/60 dark:border-slate-700">
                    <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
                      <span className="font-semibold text-teal-600 dark:text-teal-400">📌 {sessionTitle}</span>
                      <button onClick={() => toggleBookmark(message.id)}
                        className="text-amber-500 hover:text-amber-600 font-medium flex items-center gap-0.5">
                        <span className="material-icons-outlined" style={{ fontSize: 14 }}>bookmark_remove</span>
                        {locale === 'kn' ? 'ತೆಗೆದುಹಾಕಿ' : 'Remove'}
                      </button>
                    </div>
                    <p className="text-xs text-slate-800 dark:text-slate-200 line-clamp-3 leading-relaxed">
                      {message.text}
                    </p>
                    <div className="mt-2 flex items-center justify-between border-t border-slate-200 pt-2 dark:border-slate-700">
                      <span className="text-[10px] text-slate-400">
                        {message.timestamp ? new Date(message.timestamp).toLocaleString() : ''}
                      </span>
                      <button
                        onClick={() => {
                          if (sessionId) restoreSession(sessionId)
                          navigate('/app')
                          setBookmarksModalOpen(false)
                        }}
                        className="text-xs font-semibold text-teal-600 hover:underline dark:text-teal-400 flex items-center gap-1">
                        {locale === 'kn' ? 'ಚಾಟ್‌ಗೆ ಹೋಗಿ' : 'Open in Chat'} →
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
