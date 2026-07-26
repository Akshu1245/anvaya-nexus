type Props = {
  data: any
  busy?: boolean
  onDownload?: () => void
}

export function CaseBriefCard({ data, busy, onDownload }: Props) {
  if (!data) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Grounded Brief</h3>
        {data.case_snapshot?.fir_number && (
          <p className="text-xs text-slate-500">FIR: {data.case_snapshot.fir_number}</p>
        )}
      </div>
      <div className="space-y-3 px-4 py-3">
        {data.overview && (
          <div>
            <h4 className="text-xs font-semibold text-slate-600">Overview</h4>
            <p className="mt-1 text-sm text-slate-800">{data.overview}</p>
          </div>
        )}
        {data.key_findings?.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-600">Key Findings</h4>
            <ul className="mt-1 space-y-1">
              {data.key_findings.map((f: any, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                  {typeof f === 'string' ? f : f.text || f.description}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.exhibits?.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-slate-600">Exhibits ({data.exhibits.length})</h4>
            <div className="mt-1 flex flex-wrap gap-2">
              {data.exhibits.map((e: any, i: number) => (
                <span key={i} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{e.name || e.id || `Exhibit ${i + 1}`}</span>
              ))}
            </div>
          </div>
        )}
        {onDownload && (
          <button disabled={busy} onClick={onDownload} className="rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 disabled:opacity-60">
            {busy ? 'Generating...' : 'Download PDF'}
          </button>
        )}
      </div>
    </div>
  )
}
