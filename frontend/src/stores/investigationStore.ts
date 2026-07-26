import { create } from 'zustand'
import type { Investigation, Source } from '../api/m3'

type InvestigationState = {
  current: Investigation | null
  sources: Source[]
  selectedSourceIds: string[]
  results: any[]
  detail: any | null
  preview: any | null
  briefing: any | null
  trends: any | null
  related: any | null
  graph: any | null
  clusters: any | null
  priorities: any | null
  brief: any | null
  passport: any | null
  assurance: any | null
  comparison: any | null
  path: any | null
  activeCaseId: string | null
  copilot: any | null
  reasoning: any | null
  edgeExplanations: Record<string, any> | null
  shiftChanges: any | null
  supervisorReview: any | null
  checklist: any[] | null
  setCurrent: (inv: Investigation | null) => void
  setSources: (sources: Source[]) => void
  setSelectedSourceIds: (ids: string[]) => void
  setResults: (results: any[]) => void
  setDetail: (detail: any | null) => void
  setPreview: (preview: any | null) => void
  setBriefing: (data: any | null) => void
  setTrends: (data: any | null) => void
  setRelated: (data: any | null) => void
  setGraph: (data: any | null) => void
  setClusters: (data: any | null) => void
  setPriorities: (data: any | null) => void
  setBrief: (data: any | null) => void
  setPassport: (data: any | null) => void
  setAssurance: (data: any | null) => void
  setComparison: (data: any | null) => void
  setPath: (data: any | null) => void
  setActiveCaseId: (id: string | null) => void
  setCopilot: (data: any | null) => void
  setReasoning: (data: any | null) => void
  setEdgeExplanations: (data: Record<string, any> | null) => void
  setShiftChanges: (data: any | null) => void
  setSupervisorReview: (data: any | null) => void
  setChecklist: (data: any[] | null) => void
  reset: () => void
}

const initial = {
  current: null,
  sources: [],
  selectedSourceIds: ['CCTNS_REPLICA'],
  results: [],
  detail: null,
  preview: null,
  briefing: null,
  trends: null,
  related: null,
  graph: null,
  clusters: null,
  priorities: null,
  brief: null,
  passport: null,
  assurance: null,
  comparison: null,
  path: null,
  activeCaseId: null,
  copilot: null,
  reasoning: null,
  edgeExplanations: null,
  shiftChanges: null,
  supervisorReview: null,
  checklist: null,
}

export const useInvestigationStore = create<InvestigationState>((set) => ({
  ...initial,
  setCurrent: (current) => set({ current }),
  setSources: (sources) => set({ sources }),
  setSelectedSourceIds: (selectedSourceIds) => set({ selectedSourceIds }),
  setResults: (results) => set({ results }),
  setDetail: (detail) => set({ detail }),
  setPreview: (preview) => set({ preview }),
  setBriefing: (briefing) => set({ briefing }),
  setTrends: (trends) => set({ trends }),
  setRelated: (related) => set({ related }),
  setGraph: (graph) => set({ graph }),
  setClusters: (clusters) => set({ clusters }),
  setPriorities: (priorities) => set({ priorities }),
  setBrief: (brief) => set({ brief }),
  setPassport: (passport) => set({ passport }),
  setAssurance: (assurance) => set({ assurance }),
  setComparison: (comparison) => set({ comparison }),
  setPath: (path) => set({ path }),
  setActiveCaseId: (activeCaseId) => set({ activeCaseId }),
  setCopilot: (copilot) => set({ copilot }),
  setReasoning: (reasoning) => set({ reasoning }),
  setEdgeExplanations: (edgeExplanations) => set({ edgeExplanations }),
  setShiftChanges: (shiftChanges) => set({ shiftChanges }),
  setSupervisorReview: (supervisorReview) => set({ supervisorReview }),
  setChecklist: (checklist) => set({ checklist }),
  reset: () => set(initial),
}))
