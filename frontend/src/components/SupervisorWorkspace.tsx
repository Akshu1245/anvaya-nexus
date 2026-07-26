export function AuditTrail({ events }: { events: any[] }) {
  if (!events?.length) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
        </div>
        <p className="text-sm font-medium text-slate-600">No audit events</p>
        <p className="mt-1 text-xs text-slate-400">Events will appear as actions are performed.</p>
      </div>
    )
  }
  return (
    <div className="space-y-2 p-3">
      {events.map((event: any, i: number) => (
        <div key={event.id || i} className="flex gap-3 rounded-lg border border-slate-100 bg-white p-3 text-xs">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-800">{event.action || event.event_type}</span>
              <span className="shrink-0 text-[10px] text-slate-400">
                {event.timestamp ? new Date(event.timestamp).toLocaleString() : ''}
              </span>
            </div>
            <p className="mt-0.5 text-slate-500">{event.detail || event.description || ''}</p>
            {event.user && (
              <span className="mt-1 inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                {event.user}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export function ReviewTimeline({ timeline, onReview }: { timeline: any; onReview?: (id: string) => void }) {
  if (!timeline) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <p className="text-sm font-medium text-slate-600">No timeline available</p>
      </div>
    )
  }
  const stages = timeline.stages || timeline.phases || []
  return (
    <div className="space-y-3 p-3">
      {stages.map((s: any, i: number) => (
        <div key={i} className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-800">{s.name || s.stage}</span>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
              s.status === 'completed' ? 'bg-emerald-50 text-emerald-700' :
              s.status === 'in_progress' ? 'bg-blue-50 text-blue-700' :
              'bg-slate-100 text-slate-600'
            }`}>
              {s.status || 'pending'}
            </span>
          </div>
          {s.started_at && (
            <p className="mt-1 text-slate-500">{new Date(s.started_at).toLocaleString()}</p>
          )}
          {(s.actions || s.events)?.map((a: any, j: number) => (
            <div key={j} className="mt-1.5 border-t border-slate-50 pt-1.5 text-slate-600">
              {a.action || a.description}
            </div>
          ))}
          {onReview && s.review_id && (
            <button
              type="button"
              onClick={() => onReview(s.review_id)}
              className="mt-2 rounded bg-slate-100 px-2 py-1 text-[10px] font-medium hover:bg-teal-50 hover:text-teal-800"
            >
              Review
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
