import { type ReactNode, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useChatStore } from '../stores/chatStore'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

type Props = { children?: ReactNode }

export function AppShell({ children }: Props) {
  const navigate = useNavigate()
  const chatStore = useChatStore()
  const { commandPaletteOpen, setCommandPaletteOpen, mobileSidebarOpen, setMobileSidebarOpen } = useUIStore()

  // ── Keyboard shortcuts ──────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey
      if (ctrl && e.key.toLowerCase() === 'k') { e.preventDefault(); setCommandPaletteOpen(true) }
      if (ctrl && e.key.toLowerCase() === 'n') { e.preventDefault(); chatStore.reset(); navigate('/app') }
      if (e.key === 'Escape') { setCommandPaletteOpen(false); setMobileSidebarOpen(false) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [navigate, chatStore, setCommandPaletteOpen, setMobileSidebarOpen])

  const handleCommand = useCallback((action: string) => {
    setCommandPaletteOpen(false)
    switch (action) {
      case 'new-chat': chatStore.reset(); navigate('/app'); break
      case 'dashboard': navigate('/app/dashboard'); break
      case 'analytics': navigate('/app/analytics'); break
      case 'reports': navigate('/app/reports'); break
      case 'evidence': navigate('/app/evidence'); break
      case 'supervisor': navigate('/app/supervisor'); break
      case 'settings': navigate('/app/settings'); break
    }
  }, [navigate, chatStore, setCommandPaletteOpen])

  const commands = [
    { id: 'new-chat', icon: '✏️', label: 'New Chat', category: 'Navigation', shortcut: '⌘N' },
    { id: 'dashboard', icon: '📊', label: 'Dashboard', category: 'Navigation', shortcut: '' },
    { id: 'analytics', icon: '📈', label: 'Analytics', category: 'Navigation', shortcut: '' },
    { id: 'reports', icon: '📄', label: 'Reports', category: 'Navigation', shortcut: '' },
    { id: 'evidence', icon: '🗂️', label: 'Evidence', category: 'Navigation', shortcut: '' },
    { id: 'supervisor', icon: '👥', label: 'Supervisor Panel', category: 'Navigation', shortcut: '' },
    { id: 'settings', icon: '⚙️', label: 'Settings', category: 'Navigation', shortcut: '' },
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-white dark:bg-[#0f0f0f]">

      {/* Desktop sidebar */}
      <div className="hidden lg:block shrink-0">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileSidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden animate-fade-in"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 z-50 animate-slide-right lg:hidden">
            <Sidebar />
          </div>
        </>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <TopBar />
        <main
          className="flex flex-1 overflow-hidden"
          role="main"
          aria-label="Main content"
        >
          {children}
        </main>
      </div>

      {/* ── Command Palette ── */}
      {commandPaletteOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] bg-black/40 backdrop-blur-sm animate-fade-in"
          onClick={() => setCommandPaletteOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
        >
          <div
            className="w-full max-w-md rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900 animate-scale-in overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search input */}
            <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3 dark:border-slate-800">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-slate-400">
                <circle cx="11" cy="11" r="8" /><path d="M20 20l-4.3-4.3" />
              </svg>
              <input
                autoFocus
                placeholder="Search commands..."
                className="min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-200"
                onKeyDown={(e) => e.key === 'Escape' && setCommandPaletteOpen(false)}
              />
              <kbd className="shrink-0 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500">
                Esc
              </kbd>
            </div>

            {/* Command list */}
            <div className="max-h-72 overflow-y-auto p-2">
              <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Navigation</p>
              {commands.map((cmd) => (
                <button
                  key={cmd.id}
                  type="button"
                  onClick={() => handleCommand(cmd.id)}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-base dark:bg-slate-800">
                    {cmd.icon}
                  </span>
                  <span className="flex-1 font-medium text-slate-800 dark:text-slate-200">{cmd.label}</span>
                  {cmd.shortcut && (
                    <kbd className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-400 dark:border-slate-700 dark:bg-slate-800">
                      {cmd.shortcut}
                    </kbd>
                  )}
                </button>
              ))}
            </div>

            <div className="border-t border-slate-100 px-4 py-2.5 dark:border-slate-800">
              <div className="flex items-center gap-4 text-[11px] text-slate-400">
                <span><kbd className="rounded bg-slate-100 px-1 dark:bg-slate-800">↑↓</kbd> navigate</span>
                <span><kbd className="rounded bg-slate-100 px-1 dark:bg-slate-800">↵</kbd> select</span>
                <span><kbd className="rounded bg-slate-100 px-1 dark:bg-slate-800">Esc</kbd> close</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
