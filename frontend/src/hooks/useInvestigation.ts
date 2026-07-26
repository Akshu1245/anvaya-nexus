import { useCallback } from 'react'
import { m3Api } from '../api/m3'
import { useAuthStore } from '../stores/authStore'
import { useInvestigationStore } from '../stores/investigationStore'

const ROLE_PURPOSE: Record<string, string> = {
  CRIME_ANALYST: 'Pattern Research',
  SUPERVISOR: 'Supervisor Review',
}

function defaultPurpose(role?: string) {
  return role ? ROLE_PURPOSE[role] || 'Active Case Investigation' : 'Active Case Investigation'
}

export function useInvestigation() {
  const authStore = useAuthStore()
  const invStore = useInvestigationStore()

  const call = useCallback(
    async <T>(label: string, fn: () => Promise<T>): Promise<T | null> => {
      authStore.setBusy(label)
      authStore.clearError()
      try {
        return await fn()
      } catch (e) {
        authStore.setError(e instanceof Error ? e.message : 'Request failed')
        return null
      } finally {
        authStore.setBusy('')
      }
    },
    [authStore],
  )

  const ensureInvestigation = useCallback(async () => {
    if (invStore.current) return invStore.current
    const purpose = defaultPurpose(authStore.user?.role)
    const created = await m3Api.createInvestigation({
      title: 'Conversational investigation',
      purpose,
      selected_sources: invStore.selectedSourceIds.length
        ? invStore.selectedSourceIds
        : ['CCTNS_REPLICA'],
    })
    invStore.setCurrent(created)
    invStore.setSelectedSourceIds(created.selected_sources)
    return created
  }, [authStore.user?.role, invStore])

  const home = useCallback(async () => {
    const h = await m3Api.home().catch(() => null)
    const c = await m3Api
      .sourceControl(defaultPurpose(authStore.user?.role))
      .catch(() => ({ sources: [] }))
    invStore.setSources(c.sources || [])
    return { home: h, control: c }
  }, [authStore.user?.role, invStore])

  const loadSources = useCallback(async () => {
    const c = await m3Api
      .sourceControl(defaultPurpose(authStore.user?.role))
      .catch(() => ({ sources: [] }))
    invStore.setSources(c.sources || [])
    return c
  }, [authStore.user?.role, invStore])

  const preview = useCallback(
    async (query: string, parentId?: string) => {
      const inv = await ensureInvestigation()
      if (!inv) return null
      return call('preview', () =>
        parentId
          ? m3Api.followUp(inv.id, parentId, query)
          : m3Api.preview(inv.id, query),
      )
    },
    [ensureInvestigation, call],
  )

  const search = useCallback(async (plan: any) => {
    const inv = invStore.current
    if (!inv) return null
    return call('search', async () => {
      const data =
        plan.intent === 'DISCOVER'
          ? await m3Api.discover(inv.id, plan)
          : await m3Api.search(inv.id, plan)
      if (data) {
        invStore.setResults(data.results || [])
        invStore.setActiveCaseId(data.results?.[0]?.case_id || data.results?.[0]?.id || null)
      }
      return data
    })
  }, [call, invStore])

  const openCase = useCallback(
    async (caseId: string) => {
      const inv = await ensureInvestigation()
      if (!inv) return null
      return call('case', async () => {
        const data = await m3Api.case360(caseId, inv.purpose, inv.selected_sources)
        if (data) {
          invStore.setDetail(data)
          invStore.setActiveCaseId(caseId)
        }
        return data
      })
    },
    [ensureInvestigation, call, invStore],
  )

  const loadBriefing = useCallback(async () => {
    const inv = await ensureInvestigation()
    if (!inv) return null
    return call('briefing', async () => {
      const data = await m3Api.briefing(inv.id)
      if (data) invStore.setBriefing(data)
      return data
    })
  }, [ensureInvestigation, call, invStore])

  const loadTrends = useCallback(async () => {
    const inv = await ensureInvestigation()
    if (!inv) return null
    return call('trends', async () => {
      const data = await m3Api.trends(inv.id)
      if (data) invStore.setTrends(data)
      return data
    })
  }, [ensureInvestigation, call, invStore])

  const showRelated = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('related', async () => {
        const data = await m3Api.related(invStore.current!.id, caseId)
        if (data) invStore.setRelated(data)
        return data
      })
    },
    [call, invStore],
  )

  const showGraph = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('graph', async () => {
        const data = await m3Api.firGraph(invStore.current!.id, caseId)
        if (data) invStore.setGraph(data)
        return data
      })
    },
    [call, invStore],
  )

  const showClusters = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('clusters', async () => {
        const data = await m3Api.networkClusters(invStore.current!.id, caseId)
        if (data) invStore.setClusters(data)
        return data
      })
    },
    [call, invStore],
  )

  const showPriorities = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('priorities', async () => {
        const data = await m3Api.priorities(invStore.current!.id, caseId)
        if (data) invStore.setPriorities(data)
        return data
      })
    },
    [call, invStore],
  )

  const prepareBrief = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('brief', async () => {
        const data = await m3Api.brief(invStore.current!.id, caseId)
        if (data) invStore.setBrief(data)
        return data
      })
    },
    [call, invStore],
  )

  const downloadBriefPdf = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return
      await call('brief-pdf', () => m3Api.briefPdf(invStore.current!.id, caseId))
    },
    [call, invStore],
  )

  const exportConversationPdf = useCallback(
    async (turns: Array<{ role: string; text: string; kind: string; created_at: string }>) => {
      const inv = await ensureInvestigation()
      if (!inv) return
      await call('conversation-pdf', () => m3Api.conversationPdf(inv.id, turns))
    },
    [ensureInvestigation, call],
  )

  const openPassport = useCallback(
    async (id: string) => {
      const purpose = defaultPurpose(authStore.user?.role)
      return call('passport', async () => {
        const data = await m3Api.passport(id, purpose)
        if (data) invStore.setPassport(data)
        return data
      })
    },
    [authStore.user?.role, call, invStore],
  )

  const analyzeCopilot = useCallback(
    async (caseId?: string) => {
      if (!invStore.current) return null
      return call('copilot', async () => {
        const data = await m3Api.copilotAnalyze(invStore.current!.id, caseId)
        if (data) invStore.setCopilot(data)
        return data
      })
    },
    [call, invStore],
  )

  const explainFinding = useCallback(
    async (caseId: string, findingId: string) => {
      if (!invStore.current) return null
      return call('explain', async () => {
        const data = await m3Api.explainFinding(invStore.current!.id, caseId, findingId)
        if (data) invStore.setReasoning(data)
        return data
      })
    },
    [call, invStore],
  )

  const suggestNextActions = useCallback(
    async (caseId: string) => {
      if (!invStore.current) return null
      return call('copilot-suggest', async () => {
        const data = await m3Api.copilotSuggestNext(invStore.current!.id, caseId)
        if (data) invStore.setChecklist(data.checklist || data.recommended_actions || [])
        return data
      })
    },
    [call, invStore],
  )

  const loadShiftIntelligence = useCallback(
    async () => {
      const station = authStore.user?.assigned_station
      if (!station) return null
      return call('shift', async () => {
        const data = await m3Api.shiftIntelligence(station)
        if (data) invStore.setShiftChanges(data)
        return data
      })
    },
    [authStore.user?.assigned_station, call, invStore],
  )

  return {
    ...invStore,
    call,
    ensureInvestigation,
    home,
    loadSources,
    preview,
    search,
    openCase,
    loadBriefing,
    loadTrends,
    showRelated,
    showGraph,
    showClusters,
    showPriorities,
    prepareBrief,
    downloadBriefPdf,
    exportConversationPdf,
    openPassport,
    analyzeCopilot,
    explainFinding,
    suggestNextActions,
    loadShiftIntelligence,
  }
}
