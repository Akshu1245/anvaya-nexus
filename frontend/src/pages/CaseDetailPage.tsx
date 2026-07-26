import { useParams, Link } from 'react-router-dom'

export function CaseDetailPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/dashboard/search" className="text-sm text-slate-500 hover:text-slate-700">&larr; Back to search</Link>
      </div>
      <div>
        <h1 className="text-xl font-bold text-navy-950">Case {id}</h1>
        <p className="mt-1 text-sm text-slate-500">Full case detail view</p>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-400">Open a case from Search to view its 360&deg; detail here.</p>
      </div>
    </div>
  )
}
