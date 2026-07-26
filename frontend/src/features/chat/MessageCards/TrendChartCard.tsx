type Props = {
  data: any
}

export function TrendChartCard({ data }: Props) {
  if (!data?.breakdown) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Crime Trends</h3>
        {data.summary && (
          <p className="text-xs text-slate-500">{data.summary.authorised_case_count || 0} cases analyzed</p>
        )}
      </div>
      <div className="space-y-2 px-4 py-3">
        {Object.entries(data.breakdown).map(([category, count]) => (
          <div key={category} className="flex items-center gap-3">
            <span className="w-32 text-xs text-slate-600">{category.replace(/_/g, ' ')}</span>
            <div className="flex-1">
              <div className="h-5 rounded-md bg-teal-100" style={{ width: `${Math.min(Number(count) / (data.summary?.authorised_case_count || 1) * 100, 100)}%` }}>
                <div className="flex h-full items-center px-2">
                  <span className="text-xs font-medium text-teal-800">{String(count)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
