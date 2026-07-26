type Props = {
  data: any
}

export function CompareCard({ data }: Props) {
  if (!data) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Case Comparison</h3>
        {data.score !== undefined && (
          <span className="inline-block rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800">
            DNA Similarity: {Math.round(data.score * 100)}%
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 p-4">
        {data.left && (
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs font-semibold text-slate-700">{data.left.crime_number || data.left.case_id}</p>
            <p className="mt-1 text-xs text-slate-500">{data.left.offence}</p>
            <p className="text-xs text-slate-400">{data.left.station_id}</p>
          </div>
        )}
        {data.right && (
          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-xs font-semibold text-slate-700">{data.right.crime_number || data.right.case_id}</p>
            <p className="mt-1 text-xs text-slate-500">{data.right.offence}</p>
            <p className="text-xs text-slate-400">{data.right.station_id}</p>
          </div>
        )}
      </div>
      {data.shared_attributes && (
        <div className="border-t border-slate-100 px-4 py-3">
          <h4 className="text-xs font-semibold text-slate-600">Shared Attributes</h4>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {Object.entries(data.shared_attributes).map(([key, val]) => (
              <span key={key} className="rounded-md bg-teal-50 px-2 py-0.5 text-xs text-teal-800">{key}: {String(val)}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
