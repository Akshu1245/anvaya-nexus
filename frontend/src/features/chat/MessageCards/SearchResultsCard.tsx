import { useInvestigationStore } from '../../../stores/investigationStore'

type Props = {
  results: any[]
  onOpenCase: (caseId: string) => void
  onCompare?: (leftId: string, rightId: string) => void
}

export function SearchResultsCard({ results, onOpenCase, onCompare }: Props) {
  const invStore = useInvestigationStore()
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Search Results ({results.length})</h3>
      </div>
      <div className="divide-y divide-slate-100">
        {results.map((item: any, i: number) => (
          <div key={item.case_id || item.id || i} className="px-4 py-3 transition-colors hover:bg-slate-50">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{item.crime_number || item.fir_number || item.case_id}</span>
                  {item.masking?.applied && <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-900">Masked</span>}
                </div>
                <p className="mt-0.5 text-xs text-slate-500">{item.police_unit?.name || item.station_id || '—'}</p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {item.offence && <span className="rounded-md bg-red-50 px-2 py-0.5 text-xs font-medium text-red-800">{item.offence}</span>}
                  {item.status && <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{item.status}</span>}
                </div>
                {(item.registered_at || item.date) && (
                  <p className="mt-1 text-xs text-slate-400">Registered: {item.registered_at || item.date}</p>
                )}
              </div>
              <div className="flex shrink-0 gap-1.5">
                <button onClick={() => onOpenCase(item.case_id || item.id)} className="rounded-lg border border-teal-600 px-2.5 py-1 text-xs font-semibold text-teal-700 hover:bg-teal-50">360</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
