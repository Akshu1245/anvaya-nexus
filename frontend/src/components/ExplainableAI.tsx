import { useState } from 'react'

export function ConfidenceIndicator({ score, label }: { score: number; label?: string }) {
  const pct = Math.round((score || 0) * 100)
  const color =
    pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : pct >= 40 ? 'bg-orange-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-medium text-slate-500">
        {label || `${pct}% confidence`}
      </span>
    </div>
  )
}

export function SourceCitations({ sources, onOpenPassport }: { sources: string[]; onOpenPassport?: (id: string) => void }) {
  if (!sources?.length) return null
  return (
    <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">Sources</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => onOpenPassport?.(id)}
            className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 ring-1 ring-slate-200 transition-colors hover:bg-teal-50 hover:text-teal-800"
          >
            {id}
          </button>
        ))}
      </div>
    </div>
  )
}

export function ReasoningPanel({ reasoning, expanded }: { reasoning: any; expanded?: boolean }) {
  const [open, setOpen] = useState(expanded || false)
  if (!reasoning) return null
  const steps = reasoning.steps || reasoning.reasoning_steps || []
  return (
    <details open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)} className="mt-2 rounded-lg border border-slate-200 bg-white">
      <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900">
        {reasoning.title || 'Show reasoning'}
      </summary>
      <div className="space-y-2 border-t border-slate-100 px-3 py-2">
        {steps.length > 0 ? (
          steps.map((step: any, i: number) => (
            <div key={i} className="flex gap-2 text-xs">
              <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[9px] font-bold text-slate-500">
                {i + 1}
              </span>
              <div>
                <p className="font-medium text-slate-700">{step.step || step.label}</p>
                {step.detail && <p className="mt-0.5 text-slate-500">{step.detail}</p>}
              </div>
            </div>
          ))
        ) : (
          <p className="text-xs text-slate-500">{reasoning.summary || reasoning.detail || 'Reasoning available.'}</p>
        )}
        {reasoning.provenance && (
          <div className="rounded-lg bg-slate-50 p-2 text-[11px] text-slate-600">
            <span className="font-bold">Provenance: </span>
            {reasoning.provenance}
          </div>
        )}
      </div>
    </details>
  )
}

export function ProvenanceView({ provenance }: { provenance: any }) {
  if (!provenance) return null
  const records = provenance.records || provenance.sources || []
  return (
    <div className="mt-3 rounded-lg border border-slate-100 bg-white p-3 shadow-sm">
      <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">Provenance</p>
      <div className="space-y-2">
        {records.map((r: any, i: number) => (
          <div key={i} className="rounded-md bg-slate-50 p-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-700">{r.source || r.id}</span>
              <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600">
                {r.record_type || 'record'}
              </span>
            </div>
            {r.excerpt && <p className="mt-0.5 text-slate-500">"{r.excerpt}"</p>}
            {r.confidence !== undefined && <ConfidenceIndicator score={r.confidence} />}
          </div>
        ))}
      </div>
      {provenance.disclaimer && (
        <p className="mt-2 text-[10px] italic text-slate-400">{provenance.disclaimer}</p>
      )}
    </div>
  )
}

export function HumanReviewBanner({ variant = 'info' }: { variant?: 'info' | 'warning' | 'critical' }) {
  const colors = {
    info: 'border-amber-200 bg-amber-50 text-amber-800',
    warning: 'border-orange-200 bg-orange-50 text-orange-800',
    critical: 'border-red-200 bg-red-50 text-red-800',
  }
  return (
    <div className={`mt-2 rounded-lg border px-3 py-2 text-xs ${colors[variant]}`}>
      <span className="font-bold">Human review required. </span>
      AI-generated insights must be verified against original records before operational use.
    </div>
  )
}
