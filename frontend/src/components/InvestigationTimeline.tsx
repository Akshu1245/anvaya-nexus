import { useChatStore, type ChatMessage } from '../stores/chatStore'

type TimelineNode = {
  id: string
  label: string
  kind: string
  timestamp: number
  icon: string
}

const STAGE_ICONS: Record<string, string> = {
  query: 'Q',
  records: 'R',
  evidence: 'E',
  graph: 'G',
  case360: 'C',
  brief: 'B',
  dossier: 'D',
}

function classifyMessage(m: ChatMessage): TimelineNode | null {
  if (m.role !== 'assistant') return null
  if (m.kind === 'interpretation')
    return { id: m.id, label: 'Query Interpreted', kind: 'query', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.query }
  if (m.kind === 'results')
    return { id: m.id, label: 'Records Retrieved', kind: 'records', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.records }
  if (m.kind === 'case')
    return { id: m.id, label: 'Case 360 Opened', kind: 'case360', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.case360 }
  if (m.kind === 'graph')
    return { id: m.id, label: 'Relationship Analysis', kind: 'graph', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.graph }
  if (m.kind === 'answer')
    return { id: m.id, label: 'AI Analysis', kind: 'evidence', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.evidence }
  if (m.kind === 'brief')
    return { id: m.id, label: 'Brief Generated', kind: 'brief', timestamp: m.timestamp || Date.now(), icon: STAGE_ICONS.brief }
  return null
}

export function InvestigationTimeline() {
  const messages = useChatStore((s) => s.messages)
  const stage = useChatStore((s) => s.stage)

  const nodes: TimelineNode[] = messages
    .map(classifyMessage)
    .filter((n): n is TimelineNode => n !== null)

  if (nodes.length === 0) return null

  const stageColors: Record<string, string> = {
    query: 'bg-slate-100 text-slate-700 ring-slate-300',
    records: 'bg-teal-50 text-teal-800 ring-teal-300',
    case360: 'bg-blue-50 text-blue-800 ring-blue-300',
    graph: 'bg-purple-50 text-purple-800 ring-purple-300',
    evidence: 'bg-amber-50 text-amber-800 ring-amber-300',
    brief: 'bg-emerald-50 text-emerald-800 ring-emerald-300',
    dossier: 'bg-navy-50 text-navy-800 ring-navy-300',
  }

  const stageLabels: Record<string, string> = {
    ASK: 'Ask',
    DISCOVER: 'Discover',
    VERIFY: 'Verify',
    PRIORITISE: 'Prioritise',
    REPORT: 'Report',
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wide text-slate-500">Investigation Timeline</h3>
        <span className="rounded-full bg-navy-900 px-2 py-0.5 text-[10px] font-semibold text-white">
          {stageLabels[stage] || stage}
        </span>
      </div>
      <div className="relative mt-4">
        <div className="absolute left-4 top-0 h-full w-0.5 bg-slate-200" />
        <div className="space-y-3">
          {nodes.map((node, index) => {
            const isLast = index === nodes.length - 1
            return (
              <div key={node.id} className="relative flex items-start gap-3">
                <span
                  className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ring-2 ${
                    isLast
                      ? 'bg-navy-900 text-white ring-navy-400'
                      : stageColors[node.kind] || 'bg-slate-100 text-slate-500 ring-slate-200'
                  }`}
                >
                  {node.icon}
                </span>
                <div className="min-w-0 flex-1 pt-1">
                  <p className={`text-sm font-medium ${isLast ? 'text-navy-900' : 'text-slate-700'}`}>
                    {node.label}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {new Date(node.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
