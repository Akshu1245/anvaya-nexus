import { useState } from 'react'

function GapCard({ icon, title, detail, severity }: { icon: string; title: string; detail: string; severity: 'low' | 'medium' | 'high' | 'critical' }) {
  const sevColors: Record<string, string> = {
    low: 'border-slate-200 bg-white',
    medium: 'border-amber-200 bg-amber-50/50',
    high: 'border-orange-200 bg-orange-50/50',
    critical: 'border-red-200 bg-red-50/50',
  }
  return (
    <div className={`rounded-lg border p-3 text-xs ${sevColors[severity]}`}>
      <div className="flex items-start gap-2">
        <span className="mt-0.5 text-sm">{icon}</span>
        <div>
          <p className="font-semibold text-slate-800">{title}</p>
          <p className="mt-0.5 text-slate-600">{detail}</p>
        </div>
      </div>
    </div>
  )
}

function ChecklistCard({
  item,
  checked,
  onToggle,
}: {
  item: any
  checked: boolean
  onToggle: () => void
}) {
  return (
    <div className={`rounded-lg border p-3 text-xs transition-colors ${checked ? 'border-teal-200 bg-teal-50/50' : 'border-slate-100 bg-white'}`}>
      <div className="flex items-start gap-2">
        <button
          type="button"
          onClick={onToggle}
          className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
            checked ? 'border-teal-600 bg-teal-600 text-white' : 'border-slate-300 hover:border-teal-400'
          }`}
        >
          {checked && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M20 6L9 17l-5-5"/></svg>
          )}
        </button>
        <div className={checked ? 'text-slate-500 line-through' : ''}>
          <p className="font-medium text-slate-800">{item.title || item.action || 'Action item'}</p>
          {item.detail && <p className="mt-0.5 text-slate-600">{item.detail}</p>}
          {item.priority && (
            <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${
              item.priority === 'high' ? 'bg-orange-100 text-orange-800' :
              item.priority === 'critical' ? 'bg-red-100 text-red-800' :
              'bg-teal-50 text-teal-700'
            }`}>
              {item.priority}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export function CopilotPanel({ data, onAction }: { data: any; onAction?: (action: string, payload: any) => void }) {
  const [tab, setTab] = useState<'gaps' | 'suggestions' | 'briefing' | 'checklist'>('gaps')
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set())

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No copilot data</p>
        <p className="mt-1 text-xs text-slate-400">Open a case to see AI-powered investigation suggestions.</p>
      </div>
    )
  }

  const gaps = data.gaps || data.investigation_gaps || []
  const suggestions = data.suggestions || data.next_actions || []
  const briefing = data.supervisor_briefing || data.briefing_tips || []
  const checklist = data.checklist || data.recommended_actions || []

  const toggleCheck = (index: number) => {
    setCheckedItems((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const tabs = [
    { id: 'gaps' as const, label: 'Gaps', count: gaps.length },
    { id: 'suggestions' as const, label: 'Suggestions', count: suggestions.length },
    { id: 'briefing' as const, label: 'Briefing', count: briefing.length },
    { id: 'checklist' as const, label: 'Checklist', count: checklist.length },
  ]

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-1 border-b border-slate-100 px-3 py-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-md px-2 py-1 text-[11px] font-semibold transition-colors ${
              tab === t.id
                ? 'bg-navy-900 text-white'
                : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
            }`}
          >
            {t.label}{t.count > 0 ? ` (${t.count})` : ''}
          </button>
        ))}
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-3">
        {tab === 'checklist' && (
          <>
            {checklist.length === 0 && (
              <p className="py-4 text-center text-xs text-slate-400">No recommended actions yet.</p>
            )}
            {checklist.map((c: any, i: number) => (
              <ChecklistCard
                key={i}
                item={c}
                checked={checkedItems.has(i)}
                onToggle={() => toggleCheck(i)}
              />
            ))}
            {checkedItems.size > 0 && (
              <p className="pt-1 text-center text-[10px] text-slate-400">
                {checkedItems.size}/{checklist.length} completed
              </p>
            )}
          </>
        )}
        {tab === 'gaps' && (
          <>
            {gaps.length === 0 && (
              <p className="py-4 text-center text-xs text-slate-400">No gaps identified.</p>
            )}
            {gaps.map((g: any, i: number) => (
              <GapCard
                key={i}
                icon={g.icon || '⚠️'}
                title={g.title || g.gap_type || 'Investigation gap'}
                detail={g.detail || g.description || ''}
                severity={g.severity || 'medium'}
              />
            ))}
          </>
        )}
        {tab === 'suggestions' && (
          <>
            {suggestions.length === 0 && (
              <p className="py-4 text-center text-xs text-slate-400">No suggestions yet.</p>
            )}
            {suggestions.map((s: any, i: number) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
                <p className="font-medium text-slate-800">
                  <span className="text-teal-700">You may consider: </span>
                  {s.title || s.action || 'Suggested action'}
                </p>
                <p className="mt-0.5 text-slate-600">{s.detail || s.rationale || ''}</p>
                {s.priority && (
                  <span className="mt-1 inline-block rounded bg-teal-50 px-1.5 py-0.5 text-[10px] font-medium text-teal-700">
                    {s.priority}
                  </span>
                )}
                {onAction && (
                  <button
                    type="button"
                    onClick={() => onAction('suggestion', s)}
                    className="mt-2 rounded bg-slate-100 px-2 py-1 text-[10px] font-medium hover:bg-teal-50 hover:text-teal-800"
                  >
                    {s.action_label || 'Apply'}
                  </button>
                )}
              </div>
            ))}
          </>
        )}
        {tab === 'briefing' && (
          <>
            {briefing.length === 0 && (
              <p className="py-4 text-center text-xs text-slate-400">No briefing items.</p>
            )}
            {briefing.map((b: any, i: number) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
                <p className="font-medium text-slate-800">{b.title || b.topic || 'Briefing item'}</p>
                <p className="mt-0.5 text-slate-600">{b.detail || b.content || ''}</p>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  )
}
