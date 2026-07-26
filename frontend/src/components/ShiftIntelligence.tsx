export function ShiftIntelligence({ data }: { data: any }) {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No shift intelligence</p>
        <p className="mt-1 text-xs text-slate-400">Data refreshes when new FIRs or changes are detected.</p>
      </div>
    )
  }

  const sections = [
    { key: 'new_firs', label: 'New FIRs', icon: '📋', items: data.new_firs || data.new_cases || [] },
    { key: 'status_changes', label: 'Status Changes', icon: '🔄', items: data.status_changes || [] },
    { key: 'pending_evidence', label: 'Pending Evidence', icon: '📎', items: data.pending_evidence || [] },
    { key: 'upcoming_hearings', label: 'Upcoming Hearings', icon: '⚖️', items: data.upcoming_hearings || [] },
    { key: 'priority_cases', label: 'Priority Cases', icon: '🔴', items: data.priority_cases || data.priorities || [] },
    { key: 'new_entities', label: 'New Related Entities', icon: '🔗', items: data.new_entities || data.new_relations || [] },
  ].filter((s) => s.items.length > 0)

  if (sections.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-12 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-500">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">All caught up</p>
        <p className="mt-1 text-xs text-slate-400">No changes since your last shift.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 p-3">
      {sections.map((section) => (
        <div key={section.key}>
          <h4 className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            <span>{section.icon}</span>
            {section.label}
            <span className="ml-auto rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
              {section.items.length}
            </span>
          </h4>
          <div className="space-y-1.5">
            {section.items.slice(0, 5).map((item: any, i: number) => (
              <div key={item.id || i} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-slate-800">
                    {item.title || item.crime_number || item.fir_number || item.case_id || item.name || 'Item'}
                  </span>
                  {item.priority && (
                    <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium ${
                      item.priority === 'HIGH' || item.priority === 'critical'
                        ? 'bg-red-50 text-red-700'
                        : item.priority === 'MEDIUM'
                        ? 'bg-amber-50 text-amber-700'
                        : 'bg-teal-50 text-teal-700'
                    }`}>
                      {item.priority}
                    </span>
                  )}
                </div>
                {item.description && (
                  <p className="mt-0.5 text-slate-500">{item.description}</p>
                )}
                {item.station && (
                  <span className="mt-1 inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                    {item.station}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      {data.last_checked && (
        <p className="text-center text-[10px] text-slate-400">
          Last checked: {new Date(data.last_checked).toLocaleString()}
        </p>
      )}
    </div>
  )
}
