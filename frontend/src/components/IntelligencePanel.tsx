import { useState } from 'react'
import { useUIStore, type IntelligencePanelView } from '../stores/uiStore'
import { useInvestigationStore } from '../stores/investigationStore'
import { CopilotPanel } from './Copilot'
import { AuditTrail, ReviewTimeline } from './SupervisorWorkspace'
import { ShiftIntelligence } from './ShiftIntelligence'
import { ConfidenceIndicator } from './ExplainableAI'

type TabDef = {
  view: IntelligencePanelView
  label: string
}

const tabs: TabDef[] = [
  { view: 'leads', label: 'Leads' },
  { view: 'entity', label: 'Entity' },
  { view: 'evidence', label: 'Evidence' },
  { view: 'copilot', label: 'Copilot' },
  { view: 'reasoning', label: 'Reasoning' },
  { view: 'tasks', label: 'Tasks' },
  { view: 'audit', label: 'Audit' },
  { view: 'graph', label: 'Graph' },
]

function EmptyIntelligence({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l8 3v6c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/></svg>
      </div>
      <p className="text-sm font-medium text-slate-600">No {label.toLowerCase()}</p>
      <p className="mt-1 text-xs text-slate-400">Open a case to see intelligence here.</p>
    </div>
  )
}

function LeadsPanel() {
  const { related, clusters, priorities, shiftChanges } = useInvestigationStore()
  if (!related && !clusters && !priorities && !shiftChanges) return <EmptyIntelligence label="leads" />
  return (
    <div className="space-y-3 p-3">
      {shiftChanges && (
        <div>
          <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">Since Last Shift</h4>
          <ShiftIntelligence data={shiftChanges} />
        </div>
      )}
      {priorities && (
        <div>
          <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">Priorities</h4>
          <div className="space-y-2">
            {(priorities.priorities || []).slice(0, 4).map((item: any) => (
              <div key={item.id} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-slate-800">{item.title}</span>
                  <span className="shrink-0 rounded bg-teal-50 px-1.5 py-0.5 text-[10px] font-medium text-teal-700">{item.priority_band}</span>
                </div>
                {(Array.isArray(item.why) ? item.why : [item.why]).filter(Boolean).slice(0, 2).map((why: string) => (
                  <p key={why} className="mt-1 text-slate-500">{why}</p>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
      {related && (
        <div>
          <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">Related Cases</h4>
          <div className="space-y-1.5">
            {(related.related_cases || []).slice(0, 4).map((item: any) => (
              <div key={item.case_id} className="rounded-lg border border-slate-100 bg-white p-2 text-xs">
                <p className="font-medium text-slate-800">{item.crime_number || item.fir_number}</p>
                <p className="text-slate-500">{item.relationship_tier}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function EntityPanel() {
  const { detail } = useInvestigationStore()
  if (!detail) return <EmptyIntelligence label="entity" />
  const people = detail.people || {}
  const allPeople = [
    ...(people.complainants || []),
    ...(people.victims || []),
    ...(people.accused || []),
    ...(people.witnesses || []),
  ]
  if (allPeople.length === 0) return <EmptyIntelligence label="entity" />
  return (
    <div className="space-y-3 p-3">
      <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">People</h4>
      <div className="space-y-1.5">
        {allPeople.slice(0, 8).map((p: any) => (
          <div key={`${p.person_id}-${p.role_sequence}`} className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-white px-2.5 py-2 text-xs">
            <span className="font-medium text-slate-800">{p.display_name}</span>
            <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">{p.role}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function EvidencePanel() {
  const { detail } = useInvestigationStore()
  if (!detail) return <EmptyIntelligence label="evidence" />
  const evidence = detail.evidence_section?.records || detail.evidence || []
  if (evidence.length === 0) return <EmptyIntelligence label="evidence" />
  return (
    <div className="space-y-3 p-3">
      <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Evidence Records</h4>
      <div className="space-y-1.5">
        {evidence.slice(0, 6).map((e: any) => (
          <div key={e.id} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
            <p className="font-medium text-slate-800">{e.evidence_type}</p>
            <p className="mt-0.5 text-slate-500">{e.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function CopilotTab() {
  const { copilot } = useInvestigationStore()
  return <CopilotPanel data={copilot} onAction={(action, payload) => {
    // Forward to parent handler
    window.dispatchEvent(new CustomEvent('copilot-action', { detail: { action, payload } }))
  }} />
}

function ReasoningTab() {
  const { reasoning } = useInvestigationStore()
  if (!reasoning) return <EmptyIntelligence label="reasoning" />
  return (
    <div className="space-y-3 p-3">
      <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">AI Reasoning</h4>
      {reasoning.summary && (
        <div className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
          <p className="text-slate-700">{reasoning.summary}</p>
        </div>
      )}
      {reasoning.steps?.map((step: any, i: number) => (
        <div key={i} className="rounded-lg border border-slate-100 bg-white p-3 text-xs">
          <div className="flex items-start gap-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy-100 text-[10px] font-bold text-navy-800">{i + 1}</span>
            <div>
              <p className="font-medium text-slate-800">{step.label || step.step}</p>
              <p className="mt-0.5 text-slate-500">{step.detail || step.description}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function TasksPanel() {
  const { copilot } = useInvestigationStore()
  const suggestions = copilot?.suggestions || copilot?.next_actions || []
  if (suggestions.length === 0) return <EmptyIntelligence label="tasks" />
  return (
    <div className="space-y-2 p-3">
      {suggestions.map((s: any, i: number) => (
        <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-100 bg-white p-3 text-xs">
          <input type="checkbox" className="mt-0.5 h-3.5 w-3.5 rounded border-slate-300" />
          <div>
            <p className="font-medium text-slate-800">{s.title || s.action || 'Task'}</p>
            <p className="mt-0.5 text-slate-500">{s.detail || s.description || ''}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function GraphPanel() {
  const { graph } = useInvestigationStore()
  const [showAllEdges, setShowAllEdges] = useState(false)

  if (!graph) return <EmptyIntelligence label="graph" />
  const edges = graph.edges || graph.graph?.edges || []
  const nodes = graph.nodes || graph.graph?.nodes || []
  const discoveryTimeline = graph.discovery_timeline || graph.timeline || []

  return (
    <div className="space-y-3 p-3">
      {discoveryTimeline.length > 0 && (
        <div>
          <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">Discovery Timeline</h4>
          <div className="relative space-y-2 pl-4 before:absolute before:bottom-2 before:left-[7px] before:top-2 before:w-0.5 before:rounded-full before:bg-slate-200">
            {discoveryTimeline.map((event: any, i: number) => (
              <div key={i} className="relative text-xs">
                <span className="absolute -left-[13px] top-1 flex h-2.5 w-2.5 items-center justify-center rounded-full border-2 border-teal-500 bg-white" />
                <p className="font-medium text-slate-700">{event.label || event.event || 'Discovery event'}</p>
                {event.detail && <p className="text-slate-500">{event.detail}</p>}
                {event.timestamp && <p className="mt-0.5 text-[9px] text-slate-400">{new Date(event.timestamp).toLocaleString()}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">Edges ({edges.length})</h4>
          {edges.length > 3 && (
            <button
              type="button"
              onClick={() => setShowAllEdges(!showAllEdges)}
              className="text-[10px] text-teal-600 hover:text-teal-800"
            >
              {showAllEdges ? 'Show fewer' : 'Show all'}
            </button>
          )}
        </div>
        <div className="space-y-1.5">
          {(showAllEdges ? edges : edges.slice(0, 3)).map((edge: any, i: number) => (
            <div key={i} className="rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-slate-700">
                  {edge.source || edge.from} → {edge.target || edge.to}
                </span>
                <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                  {edge.relationship_type || edge.label || 'related'}
                </span>
              </div>
              {edge.explanation && <p className="mt-1 text-slate-500">{edge.explanation}</p>}
              {edge.confidence !== undefined && (
                <div className="mt-1.5">
                  <ConfidenceIndicator score={edge.confidence} label="Edge confidence" />
                </div>
              )}
              {edge.discovered_at && (
                <p className="mt-1 text-[9px] text-slate-400">Discovered: {new Date(edge.discovered_at).toLocaleString()}</p>
              )}
              {edge.supporting_evidence?.length > 0 && (
                <p className="mt-1 text-[10px] text-slate-400">
                  Evidence: {edge.supporting_evidence.map((e: any) => e.id || e).join(', ')}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
      <div>
        <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">Nodes ({nodes.length})</h4>
        <div className="flex flex-wrap gap-1.5">
          {nodes.slice(0, 8).map((node: any, i: number) => (
            <span key={node.id || i} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">
              {node.label || node.name || node.id}
            </span>
          ))}
          {nodes.length > 8 && (
            <span className="rounded-full bg-slate-50 px-2 py-0.5 text-[10px] text-slate-400">
              +{nodes.length - 8} more
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function AuditPanel() {
  const { detail } = useInvestigationStore()
  const events = detail?.audit_events || detail?.history || []
  return <AuditTrail events={events} />
}

const PANELS: Record<string, () => JSX.Element> = {
  leads: LeadsPanel,
  entity: EntityPanel,
  evidence: EvidencePanel,
  copilot: CopilotTab,
  reasoning: ReasoningTab,
  tasks: TasksPanel,
  audit: AuditPanel,
  graph: GraphPanel,
}

export function IntelligencePanel() {
  const { intelligenceOpen, intelligenceView, setIntelligenceView } = useUIStore()

  if (!intelligenceOpen) return null

  const Panel = PANELS[intelligenceView] || LeadsPanel

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-l border-slate-200 bg-white">
      <div className="flex items-center gap-1 border-b border-slate-100 px-2 py-2">
        {tabs.map((tab) => {
          const active = intelligenceView === tab.view
          return (
            <button
              key={tab.view}
              type="button"
              onClick={() => setIntelligenceView(tab.view)}
              className={`rounded-md px-2 py-1 text-[11px] font-semibold transition-colors ${
                active
                  ? 'bg-navy-900 text-white'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
              }`}
            >
              {tab.label}
            </button>
          )
        })}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <Panel />
      </div>
    </aside>
  )
}
