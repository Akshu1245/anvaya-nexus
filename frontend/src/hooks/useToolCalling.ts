import { useCallback } from 'react'
import { m3Api } from '../api/m3'
import { useChatStore, type ChatMessage } from '../stores/chatStore'
import { useInvestigationStore } from '../stores/investigationStore'

type ToolResult = {
  kind: string
  data?: any
  answer?: any
  results?: any[]
  detail?: any
  caseId?: string
}

export function useToolCalling() {
  const invStore = useInvestigationStore()
  const chatStore = useChatStore()

  const searchCases = useCallback(async (plan: any): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.search(iid, plan)
    return { kind: 'results', results: result.results }
  }, [invStore.current?.id])

  const getCase360 = useCallback(async (caseId: string, sources?: string[]): Promise<ToolResult> => {
    const purpose = invStore.current?.purpose || 'Active Case Investigation'
    const result = await m3Api.case360(caseId, purpose, sources)
    return { kind: 'case', detail: result, caseId }
  }, [invStore.current?.purpose])

  const getRelatedCases = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.related(iid, caseId)
    return { kind: 'related', data: result, caseId }
  }, [invStore.current?.id])

  const compareCases = useCallback(async (leftId: string, rightId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.compare(iid, leftId, rightId)
    return { kind: 'compare', data: result }
  }, [invStore.current?.id])

  const getGraph = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.firGraph(iid, caseId)
    return { kind: 'graph', data: result, caseId }
  }, [invStore.current?.id])

  const getTrends = useCallback(async (): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.trends(iid)
    return { kind: 'trends', data: result }
  }, [invStore.current?.id])

  const getBriefing = useCallback(async (): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.briefing(iid)
    return { kind: 'briefing', data: result }
  }, [invStore.current?.id])

  const getBrief = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.brief(iid, caseId)
    return { kind: 'brief', data: result, caseId }
  }, [invStore.current?.id])

  const getAssurance = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.firAssurance(iid, caseId)
    return { kind: 'assurance', data: result, caseId }
  }, [invStore.current?.id])

  const getPriorities = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.priorities(iid, caseId)
    return { kind: 'priorities', data: result, caseId }
  }, [invStore.current?.id])

  const getNetworkClusters = useCallback(async (caseId: string): Promise<ToolResult> => {
    const iid = invStore.current?.id
    if (!iid) throw new Error('No active investigation')
    const result = await m3Api.networkClusters(iid, caseId)
    return { kind: 'clusters', data: result, caseId }
  }, [invStore.current?.id])

  const getPassport = useCallback(async (recordId: string): Promise<ToolResult> => {
    const purpose = invStore.current?.purpose || 'Active Case Investigation'
    const result = await m3Api.passport(recordId, purpose)
    return { kind: 'passport', data: result }
  }, [invStore.current?.purpose])

  const getHome = useCallback(async (): Promise<ToolResult> => {
    const result = await m3Api.home()
    return { kind: 'home', data: result }
  }, [])

  const getSources = useCallback(async (): Promise<ToolResult> => {
    const result = await m3Api.sources()
    return { kind: 'sources', data: result }
  }, [])

  return {
    searchCases,
    getCase360,
    getRelatedCases,
    compareCases,
    getGraph,
    getTrends,
    getBriefing,
    getBrief,
    getAssurance,
    getPriorities,
    getNetworkClusters,
    getPassport,
    getHome,
    getSources,
  }
}
