import { type ReactNode } from 'react'
import { useUIStore } from '../stores/uiStore'
import { ConversationSidebar } from './ConversationSidebar'
import { IntelligencePanel } from './IntelligencePanel'

type AppLayoutProps = {
  children: ReactNode
  isConversational?: boolean
}

export function AppLayout({ children, isConversational = false }: AppLayoutProps) {
  const { sidebarOpen, toggleSidebar, intelligenceOpen, toggleIntelligence } = useUIStore()

  if (!isConversational) {
    return <div className="mx-auto max-w-7xl animate-fade-in px-5 py-7 outline-none sm:px-8 sm:py-8">{children}</div>
  }

  return (
    <div className="flex h-[calc(100vh-13rem)] animate-fade-in overflow-hidden">
      <ConversationSidebar />
      <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="absolute left-2 top-2 z-10 flex items-center gap-2">
          <button
            type="button"
            onClick={toggleSidebar}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <button
            type="button"
            onClick={toggleIntelligence}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700"
            aria-label={intelligenceOpen ? 'Close intelligence panel' : 'Open intelligence panel'}
            title={intelligenceOpen ? 'Close intelligence panel' : 'Open intelligence panel'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 3l8 3v6c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/></svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 pb-4 pt-12">
          {children}
        </div>
      </div>
      <IntelligencePanel />
    </div>
  )
}
