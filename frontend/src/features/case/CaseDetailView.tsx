import { useParams } from 'react-router-dom'

export function CaseDetailView() {
  const { id } = useParams<{ id: string }>()
  return (
    <div className="mx-auto max-w-4xl">
      <h2 className="text-lg font-bold text-slate-900">Case Detail</h2>
      <p className="mt-1 text-sm text-slate-500">Case ID: {id}</p>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-400">Full case 360 view will render here with tabs for Overview, Parties, Timeline, Evidence, Assurance, and Graph.</p>
      </div>
    </div>
  )
}
