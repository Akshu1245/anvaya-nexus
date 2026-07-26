type Props = {
  data: any
  canResolve?: boolean
  onUpdate?: (findingId: string, status: string) => void
}

export function AssuranceCard({ data, canResolve, onUpdate }: Props) {
  if (!data?.findings) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Record Assurance</h3>
        {data.summary && (
          <div className="mt-1 flex gap-3 text-xs text-slate-500">
            <span>{data.summary.open || 0} open</span>
            <span>{data.summary.acknowledged || 0} acknowledged</span>
            <span>{data.summary.resolved || 0} resolved</span>
          </div>
        )}
      </div>
      <div className="divide-y divide-slate-100">
        {data.findings.map((f: any) => (
          <div key={f.id} className="px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm text-slate-800">{f.description || f.text}</p>
                <div className="mt-1 flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    f.status === 'RESOLVED' ? 'bg-green-100 text-green-800' :
                    f.status === 'ACKNOWLEDGED' ? 'bg-amber-100 text-amber-800' :
                    'bg-red-100 text-red-800'
                  }`}>{f.status || 'OPEN'}</span>
                  {f.category && <span className="text-xs text-slate-500">{f.category}</span>}
                </div>
              </div>
              {canResolve && f.status !== 'RESOLVED' && onUpdate && (
                <div className="flex shrink-0 gap-1">
                  {f.status === 'OPEN' && (
                    <button onClick={() => onUpdate(f.id, 'ACKNOWLEDGED')} className="rounded-lg border border-amber-400 px-2 py-1 text-xs font-medium text-amber-700 hover:bg-amber-50">Acknowledge</button>
                  )}
                  {f.status === 'ACKNOWLEDGED' && (
                    <button onClick={() => onUpdate(f.id, 'RESOLVED')} className="rounded-lg border border-green-400 px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-50">Resolve</button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
