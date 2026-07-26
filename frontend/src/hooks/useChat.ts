import { useCallback, useEffect, useRef } from 'react'
import { m3Api } from '../api/m3'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import { useInvestigationStore } from '../stores/investigationStore'
import { useInvestigation } from './useInvestigation'

const CASE_TOKEN = /\b(SYN-CASE-\d{4}|SYN-FIR-[A-Z0-9-]+|SYN-CRIME-[A-Z0-9-]+)\b/i

function isBriefingAsk(text: string) {
  const t = text.toLowerCase()
  return /\b(shift\s*briefing|daily\s*briefing|my\s*briefing)\b/.test(t) || t.includes('ಬ್ರೀಫಿಂಗ್')
}

function isTrendsAsk(text: string) {
  const t = text.toLowerCase()
  return /\b(crime\s*trends?|aggregate\s*trends?|recorded\s*crime)\b/.test(t) || t.includes('ಪ್ರವೃತ್ತಿ')
}

const uid = () => Math.random().toString(36).slice(2)

const BUSY_LABELS: Record<string, string> = {
  ask: 'Interpreting question…',
  search: 'Searching records…',
  case: 'Opening Case 360…',
  brief: 'Preparing dossier…',
  'brief-pdf': 'Generating PDF…',
  'conversation-pdf': 'Exporting PDF…',
}

export function useChat() {
  const authStore = useAuthStore()
  const invStore = useInvestigationStore()
  const chatStore = useChatStore()
  const inv = useInvestigation()
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === 'function') {
      try { bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' }) } catch { /* jsdom guard */ }
    }
  }, [chatStore.messages, authStore.busy])

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

  const redactTurns = useCallback(
    (sourceMessages: typeof chatStore.messages) =>
      sourceMessages.map((m) => {
        let text = m.text || ''
        if (!text && m.kind === 'results')
          text = `Search results: ${(m.results || []).length} authorised FIR record(s).`
        if (!text && m.kind === 'briefing')
          text = `Shift briefing: ${m.data?.headline || 'loaded'}.`
        if (!text && m.kind === 'trends')
          text = `Crime trends loaded. Cases in scope: ${m.data?.summary?.authorised_case_count ?? 'n/a'}.`
        if (!text && m.kind === 'case')
          text = `Case 360 opened for ${m.caseId || 'case'}.`
        if (!text && m.kind === 'answer')
          text = m.answer?.answer || m.answer?.text || 'AI answer (source-bounded).'
        if (!text && m.kind === 'brief')
          text = `Grounded brief prepared for ${m.caseId || 'case'}.`
        if (!text) text = m.kind || 'message'
        return {
          role: m.role,
          text,
          kind: m.kind || 'text',
          created_at: new Date().toISOString(),
          summary: text,
        }
      }),
    [],
  )

  const sendMessage = useCallback(
    async (raw?: string) => {
      const text = (raw ?? chatStore.input).trim()
      if (!text || authStore.busy) return

      chatStore.setInput('')
      chatStore.addMessage({ id: uid(), role: 'user', kind: 'text', text })

      const investigation = await call('ask', () => inv.ensureInvestigation())
      if (!investigation) {
        chatStore.addMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Could not open an investigation. Check the connection and try again.',
        })
        return
      }

      const context = { active_case_id: chatStore.activeCaseId }
      const historyTurns = chatStore.messages.slice(-6).map((m) => ({
        role: m.role,
        text: m.text || m.answer?.answer || m.answer?.text || '',
      }))

      const res = await call('ask', () =>
        m3Api.chatMessage(investigation.id, { query: text, history: historyTurns, context }),
      )

      if (!res) {
        chatStore.addMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Sorry, I could not process your message right now. Please check your connection and try again.',
        })
        return
      }

      if (res.kind === 'action' && res.action_result) {
        const resolved = res.action_result
        const caseRef = resolved.case_ref || chatStore.activeCaseId
        if (resolved.action === 'BRIEFING') {
          const data = await call('briefing', () => m3Api.briefing(investigation.id))
          if (data) {
            chatStore.addMessage({ id: uid(), role: 'assistant', kind: 'briefing', data })
            chatStore.advanceStage('DISCOVER')
          }
        } else if (resolved.action === 'TRENDS') {
          const data = await call('trends', () => m3Api.trends(investigation.id))
          if (data) {
            chatStore.addMessage({ id: uid(), role: 'assistant', kind: 'trends', data })
            chatStore.advanceStage('DISCOVER')
          }
        } else if (resolved.action === 'OPEN_CASE_360' && caseRef) {
          await openCaseFromChat(caseRef)
        } else if (resolved.action === 'DOWNLOAD_PDF' && caseRef) {
          chatStore.setActiveCaseId(caseRef)
          chatStore.advanceStage('REPORT')
          const data = await call('brief', () => m3Api.brief(investigation.id, caseRef))
          if (data)
            chatStore.addMessage({ id: uid(), role: 'assistant', kind: 'brief', data, caseId: caseRef })
        } else if (resolved.action === 'CONVERSATION_PDF') {
          await doExportConversationPdf([...useChatStore.getState().messages])
        } else {
          chatStore.addMessage({
            id: uid(),
            role: 'assistant',
            kind: 'text',
            text: resolved.message || 'That guided action is not available.',
          })
        }
        return
      }

      if (res.kind === 'search_response') {
        const results = res.results || []
        const answerData = res.answer
        const plan = res.plan

        if (results.length > 0) {
          chatStore.setActiveCaseId(results[0].case_id || results[0].id || null)
          invStore.setResults(results)
        }
        chatStore.advanceStage('DISCOVER')

        if (answerData) {
          chatStore.addMessage({
            id: uid(),
            role: 'assistant',
            kind: 'answer',
            answer: answerData,
            plan,
            results,
          })
        }

        if (results.length > 0) {
          chatStore.addMessage({
            id: uid(),
            role: 'assistant',
            kind: 'results',
            results,
            plan,
          })
        }
        return
      }

      if (res.kind === 'answer' && res.answer) {
        chatStore.addMessage({
          id: uid(),
          role: 'assistant',
          kind: 'answer',
          answer: res.answer,
        })
        return
      }

      chatStore.addMessage({
        id: uid(),
        role: 'assistant',
        kind: 'text',
        text: typeof res.answer === 'string' ? res.answer : 'I have processed your request.',
      })
    },
    [chatStore, authStore.busy, inv, call, redactTurns, invStore],
  )

  const runSearch = useCallback(
    async (messageId: string, preview: any) => {
      const investigation = invStore.current
      if (!investigation) return

      const base = preview.normalised_interpretation
      const plan = { ...base, filters: { ...base.filters } }
      chatStore.updateMessage(messageId, { confirmed: true })

      const data = await call('search', () =>
        plan.intent === 'DISCOVER'
          ? m3Api.discover(investigation.id, plan)
          : m3Api.search(investigation.id, plan),
      )

      if (!data) return
      const results = data.results || []

      if (results.length === 0) {
        chatStore.addMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'No authorised synthetic records matched those filters.',
        })
        return
      }

      chatStore.setActiveCaseId(results[0].case_id || results[0].id || null)
      chatStore.advanceStage('DISCOVER')
      chatStore.addMessage({ id: uid(), role: 'assistant', kind: 'results', results, plan })
      invStore.setResults(results)

      if (results.length > 0) {
        const question =
          [...useChatStore.getState().messages].reverse().find((m) => m.role === 'user' && m.text)?.text || ''
        const answerData = await call('answer', () =>
          m3Api.aiAnswer(investigation.id, { plan, question, results }),
        )
        if (answerData)
          chatStore.addMessage({
            id: uid(),
            role: 'assistant',
            kind: 'answer',
            answer: answerData,
            plan,
            results,
          })
      }
    },
    [invStore, chatStore, call],
  )

  const openCaseFromChat = useCallback(
    async (caseId: string) => {
      const investigation = await call('case', () => inv.ensureInvestigation())
      if (!investigation) return
      const detail = await call('case', () =>
        m3Api.case360(caseId, investigation.purpose, investigation.selected_sources),
      )
      if (detail) {
        const id = detail?.case?.id || detail?.overview?.id || caseId
        chatStore.setActiveCaseId(id)
        chatStore.advanceStage('VERIFY')
        chatStore.addMessage({ id: uid(), role: 'assistant', kind: 'case', detail, caseId: id })
        invStore.setDetail(detail)
      }
    },
    [call, inv, chatStore, invStore],
  )

  const doExportConversationPdf = useCallback(
    async (sourceMessages = useChatStore.getState().messages) => {
      const done = await call('conversation-pdf', async () => {
        const investigation = await inv.ensureInvestigation()
        await m3Api.conversationPdf(investigation.id, redactTurns(sourceMessages))
        return true
      })
      if (done)
        chatStore.addMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Conversation PDF downloaded.',
        })
    },
    [chatStore, call, inv, redactTurns],
  )

  const reset = useCallback(() => {
    chatStore.reset()
    invStore.reset()
  }, [chatStore, invStore])

  return {
    messages: chatStore.messages,
    input: chatStore.input,
    setInput: chatStore.setInput,
    parentMessageId: chatStore.parentMessageId,
    setParentMessageId: chatStore.setParentMessageId,
    stage: chatStore.stage,
    maxStage: chatStore.maxStage,
    advanceStage: chatStore.advanceStage,
    helpOpen: chatStore.helpOpen,
    setHelpOpen: chatStore.setHelpOpen,
    coachStep: chatStore.coachStep,
    setCoachStep: chatStore.setCoachStep,
    conversationTitle: chatStore.conversationTitle,
    setConversationTitle: chatStore.setConversationTitle,
    bottomRef,
    busy: authStore.busy,
    error: authStore.error,
    sendMessage,
    runSearch,
    openCase: openCaseFromChat,
    exportPdf: doExportConversationPdf,
    reset,
    addMessage: chatStore.addMessage,
    updateMessage: chatStore.updateMessage,
    dismissCoach: () => {
      try {
        localStorage.setItem('anvaya_coach_v1', 'dismissed')
      } catch {
        /* noop */
      }
      chatStore.setCoachStep(-1)
    },
  }
}
