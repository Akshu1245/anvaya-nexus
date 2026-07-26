import { useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'
import { useUIStore } from '../stores/uiStore'
import { useAuthStore } from '../stores/authStore'
import { m3Api } from '../api/m3'

// ── Icons ────────────────────────────────────────────────────────────────────
const ICN = {
  home: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  dashboard: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" /><rect x="14" y="3" width="7" height="5" /><rect x="14" y="12" width="7" height="9" /><rect x="3" y="16" width="7" height="5" />
    </svg>
  ),
  analytics: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 20V10M12 20V4M6 20v-6" />
    </svg>
  ),
  reports: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  supervisor: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  evidence: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="21 8 21 21 3 21 3 8" /><rect x="1" y="3" width="22" height="5" /><line x1="10" y1="12" x2="14" y2="12" />
    </svg>
  ),
  search: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  plus: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  pin: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" stroke="none">
      <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2z" />
    </svg>
  ),
  settings: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.32 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  ),
  logout: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  sun: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  ),
  moon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
    </svg>
  ),
  chevronRight: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 18l6-6-6-6" />
    </svg>
  ),
  edit: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  trash: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
    </svg>
  ),
  archive: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="21 8 21 21 3 21 3 8" /><rect x="1" y="3" width="22" height="5" /><line x1="10" y1="12" x2="14" y2="12" />
    </svg>
  ),
}

// ── Session item with context menu ───────────────────────────────────────────
function SessionRow({ session, isActive, onSelect, onRename, onPin, onArchive, onDelete }: {
  session: any; isActive: boolean
  onSelect: () => void; onRename: () => void; onPin: () => void; onArchive: () => void; onDelete: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className={`group relative flex items-center gap-1 rounded-lg pr-1 text-sm transition-colors ${isActive ? 'bg-slate-200/60 dark:bg-slate-700/60' : 'hover:bg-slate-100 dark:hover:bg-slate-800/60'}`}>
      <button
        type="button"
        onClick={onSelect}
        className="flex min-w-0 flex-1 items-center gap-2.5 px-3 py-2 text-left"
      >
        {session.pinned && <span className="shrink-0 text-amber-400">{ICN.pin}</span>}
        <span className={`truncate text-xs font-medium ${isActive ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`}>
          {session.title}
        </span>
      </button>

      {/* 3-dot menu — only on hover */}
      <div className="relative shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setMenuOpen((p) => !p) }}
          className="flex h-6 w-6 items-center justify-center rounded-md text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
          aria-label="Session options"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" /></svg>
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-7 z-20 w-40 rounded-xl border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
              {[
                { icon: ICN.edit, label: 'Rename', action: onRename },
                { icon: ICN.pin, label: session.pinned ? 'Unpin' : 'Pin', action: onPin },
                { icon: ICN.archive, label: 'Archive', action: onArchive },
                { icon: ICN.trash, label: 'Delete', action: onDelete },
              ].map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => { item.action(); setMenuOpen(false) }}
                  className={`flex w-full items-center gap-2.5 px-3 py-1.5 text-xs hover:bg-slate-50 dark:hover:bg-slate-800 ${item.label === 'Delete' ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-300'}`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ── Time-grouped conversations ───────────────────────────────────────────────
function groupSessions(sessions: any[]) {
  const now = Date.now(); const day = 86400000
  const g: { label: string; items: any[] }[] = []
  const todaySessions = sessions.filter((s) => now - s.updatedAt < day)
  if (todaySessions.length) g.push({ label: 'Today', items: todaySessions })
  const yesterdaySessions = sessions.filter((s) => now - s.updatedAt >= day && now - s.updatedAt < day * 2)
  if (yesterdaySessions.length) g.push({ label: 'Yesterday', items: yesterdaySessions })
  const thisWeekSessions = sessions.filter((s) => now - s.updatedAt >= day * 2 && now - s.updatedAt < day * 7)
  if (thisWeekSessions.length) g.push({ label: 'This Week', items: thisWeekSessions })
  const olderSessions = sessions.filter((s) => now - s.updatedAt >= day * 7)
  if (olderSessions.length) g.push({ label: 'Earlier', items: olderSessions })
  return g
}

// ── Main Sidebar ─────────────────────────────────────────────────────────────
export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const chatStore = useChatStore()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const { darkMode, toggleDarkMode } = useUIStore()
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const isActive = (path: string) => {
    if (path === '/app') return location.pathname === '/app' || location.pathname.startsWith('/app/chat')
    return location.pathname.startsWith(path)
  }

  const handleNewChat = useCallback(() => {
    chatStore.reset()
    navigate('/app')
  }, [chatStore, navigate])

  const handleSelectSession = useCallback((id: string) => {
    chatStore.restoreSession(id)
    navigate('/app')
  }, [chatStore, navigate])

  const handleLogout = useCallback(async () => {
    await m3Api.logout().catch(() => {})
    setUser(null)
    navigate('/auth/login', { replace: true })
  }, [setUser, navigate])

  const startRename = (session: any) => {
    setRenaming(session.id)
    setRenameValue(session.title)
  }

  const commitRename = () => {
    if (renaming && renameValue.trim()) {
      chatStore.renameSession(renaming, renameValue.trim())
    }
    setRenaming(null)
  }

  const pinned = chatStore.sessions.filter((s) => s.pinned && !s.archived)
  const recent = chatStore.sessions.filter((s) => !s.pinned && !s.archived)
  const filtered = chatStore.sessionSearch
    ? recent.filter((s) => s.title.toLowerCase().includes(chatStore.sessionSearch.toLowerCase()))
    : recent
  const groups = groupSessions(filtered)

  // Nav sections
  const mainNav = [
    { id: 'home', path: '/app', label: 'AI Chat', icon: ICN.home },
    { id: 'dashboard', path: '/app/dashboard', label: 'Dashboard', icon: ICN.dashboard },
    { id: 'analytics', path: '/app/analytics', label: 'Analytics', icon: ICN.analytics },
    { id: 'reports', path: '/app/reports', label: 'Reports', icon: ICN.reports },
    { id: 'evidence', path: '/app/evidence', label: 'Evidence', icon: ICN.evidence },
  ]
  const supervisorNav = user?.role === 'SUPERVISOR'
    ? [{ id: 'supervisor', path: '/app/supervisor', label: 'Supervisor', icon: ICN.supervisor }]
    : []

  const userInitial = (user?.username || 'U').charAt(0).toUpperCase()
  const displayName = user?.username?.split('.')?.[0] || user?.username || 'User'
  const roleName = user?.role?.replace(/_/g, ' ') || ''

  return (
    <aside className="flex h-screen w-64 flex-col border-r" style={{ background: '#0d1f3c', borderColor: 'rgba(200,168,75,0.3)' }}>

      {/* ── Logo / Brand ── */}
      <div className="flex items-center justify-between px-3 py-3 border-b" style={{ borderColor: 'rgba(200,168,75,0.2)', background: 'rgba(0,0,0,0.2)' }}>
        <button onClick={() => navigate('/app')} className="flex items-center gap-2.5 group min-w-0">
          <img src="/ksp_logo_real.png" alt="KSP" className="h-9 w-9 object-contain rounded-full shrink-0"
            style={{ border: '1px solid #c8a84b', background: '#fff' }} />
          <div className="min-w-0">
            <p className="text-[9px] font-bold uppercase tracking-widest" style={{ color: '#c8a84b' }}>Karnataka Police</p>
            <p className="text-xs font-bold text-white truncate">ANVAYA NEXUS</p>
          </div>
        </button>
        <button
          onClick={handleNewChat}
          className="flex h-7 w-7 items-center justify-center rounded-lg transition-colors shrink-0"
          style={{ color: '#c8a84b', background: 'rgba(200,168,75,0.1)', border: '1px solid rgba(200,168,75,0.2)' }}
          title="New Chat (Ctrl+N)"
          aria-label="New Chat"
        >
          {ICN.plus}
        </button>
      </div>

      {/* ── Navigation ── */}
      <div className="px-2 pt-3 pb-2">
        {[...mainNav, ...supervisorNav].map((n) => (
          <button
            key={n.id}
            onClick={() => navigate(n.path)}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors mb-0.5`}
            style={isActive(n.path) ? {
              background: 'rgba(200,168,75,0.15)',
              color: '#c8a84b',
              border: '1px solid rgba(200,168,75,0.25)',
            } : {
              color: '#93b8e8',
              border: '1px solid transparent',
            }}
          >
            <span className="shrink-0" style={{ color: isActive(n.path) ? '#c8a84b' : '#4a6a90' }}>{n.icon}</span>
            {n.label}
          </button>
        ))}
      </div>

      {/* ── Conversations ── */}
      <div className="flex-1 overflow-y-auto px-2 pb-2" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(200,168,75,0.2) transparent' }}>

        {/* Search */}
        <div className="relative mb-2">
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4a6a90' }}>{ICN.search}</span>
          <input
            type="search"
            value={chatStore.sessionSearch}
            onChange={(e) => chatStore.setSessionSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full rounded-lg py-1.5 pl-8 pr-3 text-xs outline-none"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(200,168,75,0.15)', color: '#93b8e8' }}
          />
        </div>

        {/* Pinned */}
        {pinned.length > 0 && (
          <div className="mb-2">
            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#4a6a90' }}>Pinned</p>
            {pinned.map((s) => (
              <div key={s.id}>
                {renaming === s.id ? (
                  <input
                    autoFocus
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onBlur={commitRename}
                    onKeyDown={(e) => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenaming(null) }}
                    className="mx-3 my-1 w-[calc(100%-1.5rem)] rounded-md border border-teal-400 bg-white px-2 py-1 text-xs outline-none dark:bg-slate-800 dark:text-white"
                  />
                ) : (
                  <SessionRow
                    session={s}
                    isActive={chatStore.currentSessionId === s.id}
                    onSelect={() => handleSelectSession(s.id)}
                    onRename={() => startRename(s)}
                    onPin={() => chatStore.pinSession(s.id)}
                    onArchive={() => chatStore.archiveSession(s.id)}
                    onDelete={() => chatStore.removeSession(s.id)}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Grouped history */}
        {groups.map((group) => (
          <div key={group.label} className="mb-2">
            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#4a6a90' }}>{group.label}</p>
            {group.items.map((s) => (
              <div key={s.id}>
                {renaming === s.id ? (
                  <input
                    autoFocus
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                    onBlur={commitRename}
                    onKeyDown={(e) => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenaming(null) }}
                    className="mx-3 my-1 w-[calc(100%-1.5rem)] rounded-md border border-teal-400 bg-white px-2 py-1 text-xs outline-none dark:bg-slate-800 dark:text-white"
                  />
                ) : (
                  <SessionRow
                    session={s}
                    isActive={chatStore.currentSessionId === s.id}
                    onSelect={() => handleSelectSession(s.id)}
                    onRename={() => startRename(s)}
                    onPin={() => chatStore.pinSession(s.id)}
                    onArchive={() => chatStore.archiveSession(s.id)}
                    onDelete={() => chatStore.removeSession(s.id)}
                  />
                )}
              </div>
            ))}
          </div>
        ))}

        {/* Empty state */}
        {chatStore.sessions.filter((s) => !s.archived).length === 0 && (
          <div className="px-4 py-8 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl" style={{ background: 'rgba(200,168,75,0.1)', border: '1px solid rgba(200,168,75,0.2)' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: '#4a6a90' }}>
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </div>
            <p className="text-xs font-medium" style={{ color: '#4a6a90' }}>No conversations yet</p>
            <p className="mt-1 text-[10px]" style={{ color: '#2a4060' }}>Start a new investigation above</p>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="p-2 space-y-0.5" style={{ borderTop: '1px solid rgba(200,168,75,0.2)' }}>
        <button
          onClick={() => navigate('/app/settings')}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
          style={{ color: '#93b8e8' }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(200,168,75,0.08)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <span className="shrink-0" style={{ color: '#4a6a90' }}>{ICN.settings}</span>
          Settings
        </button>
        <button
          onClick={toggleDarkMode}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors"
          style={{ color: '#93b8e8' }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(200,168,75,0.08)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <span className="shrink-0" style={{ color: '#4a6a90' }}>{darkMode ? ICN.sun : ICN.moon}</span>
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>

        {/* User info row */}
        <div className="flex items-center gap-2.5 rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(200,168,75,0.15)' }}>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-bold text-xs" style={{ background: 'linear-gradient(135deg, #c8a84b, #e8c96b)', color: '#0d1f3c' }}>
            {userInitial}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-white">{displayName}</p>
            <p className="text-[10px]" style={{ color: '#4a6a90' }}>{roleName}</p>
          </div>
          <button
            onClick={handleLogout}
            className="shrink-0 rounded-lg p-1 transition-colors"
            style={{ color: '#4a6a90' }}
            title="Sign out"
            aria-label="Sign out"
            onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#4a6a90')}
          >
            {ICN.logout}
          </button>
        </div>
      </div>
    </aside>
  )
}
