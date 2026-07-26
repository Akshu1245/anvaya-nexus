import { useState } from 'react'

export function ConfidenceIndicator({ score, label }: { score: number; label?: string }) {
  const pct = Math.round((score || 0) * 100)
  const color =
    pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : pct >= 40 ? 'bg-orange-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-semibold text-slate-800 dark:text-slate-200">
        {label || `${pct}% confidence`}
      </span>
    </div>
  )
}

export function SourceCitations({ sources, onOpenPassport }: { sources: string[]; onOpenPassport?: (id: string) => void }) {
  if (!sources?.length) return null
  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/80 p-3 dark:border-slate-700 dark:bg-slate-800/60">
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-slate-700 dark:text-slate-300">Sources</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => onOpenPassport?.(id)}
            className="rounded bg-white px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-800 ring-1 ring-slate-300 transition-colors hover:bg-teal-50 hover:text-teal-900 dark:bg-slate-700 dark:text-slate-100 dark:ring-slate-600 dark:hover:bg-teal-950 dark:hover:text-teal-200"
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
    <details open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)} className="mt-2.5 rounded-xl border border-slate-200 bg-slate-50/80 text-xs dark:border-slate-700 dark:bg-slate-800/60">
      <summary className="cursor-pointer px-3 py-2 font-bold text-slate-800 hover:text-slate-950 dark:text-slate-200 dark:hover:text-white">
        {reasoning.title || 'Show reasoning'}
      </summary>
      <div className="space-y-2 border-t border-slate-200 px-3 py-2 dark:border-slate-700">
        {steps.length > 0 ? (
          steps.map((step: any, i: number) => (
            <div key={i} className="flex gap-2 text-xs">
              <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[9px] font-bold text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                {i + 1}
              </span>
              <div>
                <p className="font-semibold text-slate-900 dark:text-slate-100">{step.step || step.label}</p>
                {step.detail && <p className="mt-0.5 text-slate-700 dark:text-slate-300">{step.detail}</p>}
              </div>
            </div>
          ))
        ) : (
          <p className="text-xs text-slate-700 dark:text-slate-300">{reasoning.summary || reasoning.detail || 'Reasoning available.'}</p>
        )}
        {reasoning.provenance && (
          <div className="rounded-lg bg-slate-100 p-2 text-[11px] font-medium text-slate-800 dark:bg-slate-700/80 dark:text-slate-200">
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
    <div className="mt-3 rounded-lg border border-slate-100 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-[#161b26]">
      <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-600 dark:text-slate-400">Provenance</p>
      <div className="space-y-2">
        {records.map((r: any, i: number) => (
          <div key={i} className="rounded-md bg-slate-50 p-2 text-xs dark:bg-slate-800">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 dark:text-slate-100">{r.source || r.id}</span>
              <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                {r.record_type || 'record'}
              </span>
            </div>
            {r.excerpt && <p className="mt-0.5 text-slate-700 dark:text-slate-300">"{r.excerpt}"</p>}
            {r.confidence !== undefined && <ConfidenceIndicator score={r.confidence} />}
          </div>
        ))}
      </div>
      {provenance.disclaimer && (
        <p className="mt-2 text-[10px] italic text-slate-500 dark:text-slate-400">{provenance.disclaimer}</p>
      )}
    </div>
  )
}

export function HumanReviewBanner({ variant = 'info' }: { variant?: 'info' | 'warning' | 'critical' }) {
  const colors = {
    info: 'border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-700/80 dark:bg-amber-950/70 dark:text-amber-100',
    warning: 'border-orange-300 bg-orange-50 text-orange-950 dark:border-orange-700/80 dark:bg-orange-950/70 dark:text-orange-100',
    critical: 'border-red-300 bg-red-50 text-red-950 dark:border-red-700/80 dark:bg-red-950/70 dark:text-red-100',
  }
  return (
    <div className={`mt-2.5 rounded-lg border px-3 py-2 text-xs leading-relaxed font-semibold ${colors[variant]}`}>
      <span className="font-bold uppercase tracking-wider">Human review required: </span>
      AI-generated insights must be verified against original records before operational use.
    </div>
  )
}
