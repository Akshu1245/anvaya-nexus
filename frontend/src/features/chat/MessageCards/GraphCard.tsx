type Props = {
  data: any
  onOpenCase?: (caseId: string) => void
}

export function GraphCard({ data, onOpenCase }: Props) {
  if (!data?.graph) return null
  const g = data.graph
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-bubble">
      <div className="border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-800">Relationship Graph</h3>
        <p className="text-xs text-slate-500">{g.node_count || 0} nodes · {g.edge_count || 0} edges</p>
      </div>
      <div className="space-y-1.5 px-4 py-3">
        {g.nodes?.slice(0, 10).map((node: any, i: number) => (
          <div key={node.id || i} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-700">{node.label || node.id}</p>
              {node.type && <p className="text-[10px] text-slate-500">{node.type}</p>}
            </div>
            {onOpenCase && (
              <button onClick={() => onOpenCase(node.id)} className="rounded border border-slate-300 px-2 py-0.5 text-[10px] text-slate-600 hover:bg-slate-200">Open</button>
            )}
          </div>
        ))}
        {(g.nodes?.length || 0) > 10 && (
          <p className="text-center text-[10px] text-slate-400">+{g.nodes.length - 10} more nodes</p>
        )}
      </div>
      <div className="border-t border-slate-100 px-4 py-2">
        <details>
          <summary className="cursor-pointer text-xs font-semibold text-slate-600">Edge details ({g.edges?.length || 0})</summary>
          <div className="mt-2 space-y-1">
            {g.edges?.slice(0, 20).map((edge: any, i: number) => (
              <div key={i} className="rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
                <span className="font-medium">{edge.source || edge.from}</span> → <span className="font-medium">{edge.target || edge.to}</span>
                <span className="ml-1.5 rounded bg-slate-200 px-1 text-[9px]">{edge.relationship_type || edge.label || 'related'}</span>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}
