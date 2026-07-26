import { useParams } from 'react-router-dom'

export function WorkspaceView() {
  const { id } = useParams<{ id: string }>()
  return (
    <div className="mx-auto max-w-4xl">
      <h2 className="text-lg font-bold text-slate-900">Investigation Workspace</h2>
      <p className="mt-1 text-sm text-slate-500">ID: {id}</p>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-400">Full investigation workspace with source control, timeline, and case management will render here.</p>
      </div>
    </div>
  )
}
