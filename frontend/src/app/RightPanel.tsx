import { useUIStore } from '../stores/uiStore'
import { useInvestigationStore } from '../stores/investigationStore'
import { useAuthStore } from '../stores/authStore'

export function RightPanel() {
  const { intelligenceOpen, setIntelligenceOpen } = useUIStore()
  const invStore = useInvestigationStore()
  const user = useAuthStore((s) => s.user)
  const hasInvestigation = !!invStore.current
  const hasResults = (invStore.results?.length || 0) > 0

  if (!intelligenceOpen) return null

  return (
    <aside className="hidden w-72 flex-col border-l border-slate-200 bg-white dark:border-slate-700 dark:bg-navy-950 lg:flex animate-slide-right">
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-3 dark:border-slate-700">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Context</span>
        <button onClick={() => setIntelligenceOpen(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">User</p>
          <p className="mt-1 text-xs font-medium text-slate-800 dark:text-slate-200">{user?.username}</p>
          <p className="text-[10px] text-slate-500 dark:text-slate-400">{user?.role?.replace(/_/g, ' ')}</p>
          <p className="text-[10px] text-slate-500 dark:text-slate-400">{user?.assigned_station || '—'}</p>
        </div>

        {hasInvestigation && (
          <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Investigation</p>
            <p className="mt-1 text-xs font-medium text-slate-800 dark:text-slate-200">{invStore.current?.title}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">{invStore.current?.purpose}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {invStore.current?.selected_sources?.slice(0, 3).map((s: string) => (
                <span key={s} className="rounded-full bg-teal-100 px-1.5 py-0.5 text-[9px] font-medium text-teal-800 dark:bg-teal-900/30 dark:text-teal-300">{s}</span>
              ))}
            </div>
          </div>
        )}

        {hasResults && (
          <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Results</p>
            <p className="mt-1 text-lg font-bold text-slate-800 dark:text-slate-200">{invStore.results?.length || 0}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">cases found</p>
            {invStore.activeCaseId && (
              <p className="mt-1 text-[10px] text-teal-600 dark:text-teal-400">Active: {invStore.activeCaseId}</p>
            )}
          </div>
        )}

        <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">AI Suggestions</p>
          <div className="mt-2 space-y-1.5">
            <button className="w-full rounded-lg bg-gradient-to-r from-teal-50 to-teal-100/50 px-3 py-2 text-left text-[10px] font-medium text-teal-800 transition-colors hover:from-teal-100 hover:to-teal-200 dark:from-teal-900/30 dark:to-teal-900/10 dark:text-teal-300 dark:hover:from-teal-900/50">
              💡 Search related cases
            </button>
            <button className="w-full rounded-lg bg-gradient-to-r from-purple-50 to-purple-100/50 px-3 py-2 text-left text-[10px] font-medium text-purple-800 transition-colors hover:from-purple-100 hover:to-purple-200 dark:from-purple-900/30 dark:to-purple-900/10 dark:text-purple-300 dark:hover:from-purple-900/50">
              💡 Generate investigation brief
            </button>
            <button className="w-full rounded-lg bg-gradient-to-r from-amber-50 to-amber-100/50 px-3 py-2 text-left text-[10px] font-medium text-amber-800 transition-colors hover:from-amber-100 hover:to-amber-200 dark:from-amber-900/30 dark:to-amber-900/10 dark:text-amber-300 dark:hover:from-amber-900/50">
              💡 Compare with similar cases
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Quick Actions</p>
          <div className="mt-2 grid grid-cols-2 gap-1.5">
            <button className="rounded-lg border border-slate-200 px-2 py-1.5 text-[10px] font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800">Export PDF</button>
            <button className="rounded-lg border border-slate-200 px-2 py-1.5 text-[10px] font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800">Share</button>
            <button className="rounded-lg border border-slate-200 px-2 py-1.5 text-[10px] font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800">Add Note</button>
            <button className="rounded-lg border border-slate-200 px-2 py-1.5 text-[10px] font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800">Bookmark</button>
          </div>
        </div>
      </div>
    </aside>
  )
}
