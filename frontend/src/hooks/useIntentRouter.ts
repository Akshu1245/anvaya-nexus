import { useCallback } from 'react'
import { m3Api } from '../api/m3'
import { useChatStore } from '../stores/chatStore'
import { useInvestigationStore } from '../stores/investigationStore'

type Intent = 'search' | 'case' | 'compare' | 'trends' | 'briefing' | 'graph' | 'report' | 'evidence' | 'summarize' | 'translate' | 'export' | 'navigate' | 'unknown'

const uid = () => Math.random().toString(36).slice(2)

const INTENT_PATTERNS: { pattern: RegExp; intent: Intent }[] = [
  { pattern: /\b(find|search|look|show)\b.*\b(FIR|case|record)s?\b/i, intent: 'search' },
  { pattern: /\bsummarize\b|\bcase\s*360\b|\bopen\b.*\bcase\b/i, intent: 'case' },
  { pattern: /\bcompare\b.*\bcases?\b|\bdna\b|\bsimilarity\b/i, intent: 'compare' },
  { pattern: /\btrends?\b|\baggregate\b|\bstatistics?\b|\bchart\b/i, intent: 'trends' },
  { pattern: /\bbrief(ing)?\b|\bshift\b|\bdaily\b.*\breport\b/i, intent: 'briefing' },
  { pattern: /\bgraph\b|\bnetwork\b|\brelationship\b|\bmap\b/i, intent: 'graph' },
  { pattern: /\b(report|draft|create.*report)\b/i, intent: 'report' },
  { pattern: /\bevidence\b|\bexhibit\b|\bpassport\b|\bsource\b/i, intent: 'evidence' },
  { pattern: /\btranslate\b/i, intent: 'translate' },
  { pattern: /\bexport\b|\bdownload\b|\bpdf\b/i, intent: 'export' },
]

function classifyIntent(text: string): Intent {
  for (const { pattern, intent } of INTENT_PATTERNS) {
    if (pattern.test(text)) return intent
  }
  return 'unknown'
}

export function useIntentRouter() {
  const chatStore = useChatStore()
  const invStore = useInvestigationStore()

  const dispatch = useCallback(async (text: string) => {
    const intent = classifyIntent(text)
    const iid = invStore.current?.id

    switch (intent) {
      case 'search': {
        if (!iid) return { kind: 'text', text: 'Please start an investigation first.' }
        const preview = await m3Api.preview(iid, text).catch(() => null)
        if (!preview) return { kind: 'text', text: 'Could not interpret that query.' }
        chatStore.setParentMessageId(preview.message_id || '')
        return { kind: 'interpretation', preview }
      }
      case 'case': {
        const match = text.match(/\b(SYN-(?:FIR|CASE|CRIME)-\d+|[A-Z0-9-]+)/i)
        const caseId = match?.[1] || invStore.activeCaseId
        if (!caseId || !iid) return { kind: 'text', text: 'Specify a case ID or select one first.' }
        const detail = await m3Api.case360(caseId, invStore.current?.purpose || 'Active Case Investigation').catch(() => null)
        if (!detail) return { kind: 'text', text: 'Case not found.' }
        return { kind: 'case', detail, caseId }
      }
      case 'trends': {
        if (!iid) return { kind: 'text', text: 'Please start an investigation first.' }
        const trends = await m3Api.trends(iid).catch(() => null)
        if (!trends) return { kind: 'text', text: 'Could not load trends.' }
        return { kind: 'trends', data: trends }
      }
      case 'briefing': {
        if (!iid) return { kind: 'text', text: 'Please start an investigation first.' }
        const briefing = await m3Api.briefing(iid).catch(() => null)
        if (!briefing) return { kind: 'text', text: 'Could not load briefing.' }
        return { kind: 'briefing', data: briefing }
      }
      case 'compare': {
        const ids = text.match(/\b(SYN-(?:FIR|CASE|CRIME)-\d+)/gi)
        if (!ids || ids.length < 2 || !iid) return { kind: 'text', text: 'Please specify two case IDs to compare.' }
        const data = await m3Api.compare(iid, ids[0], ids[1]).catch(() => null)
        if (!data) return { kind: 'text', text: 'Could not compare cases.' }
        return { kind: 'compare', data }
      }
      case 'report': {
        if (!iid) return { kind: 'text', text: 'Please start an investigation first.' }
        const report = await m3Api.createReport({ investigation_id: iid, title: text.replace(/create.*report/i, '').trim() || 'Investigation Report' }).catch(() => null)
        if (!report) return { kind: 'text', text: 'Could not create report.' }
        return { kind: 'text', text: `Report created: ${report.report_id || report.id}. You can now add sections and submit for review.` }
      }
      case 'evidence': {
        const match = text.match(/\b(SYN-(?:FIR|CASE|CRIME)-\d+|[A-Z0-9-]+)/i)
        const caseId = match?.[1] || invStore.activeCaseId
        if (!caseId || !iid) return { kind: 'text', text: 'Specify a case to view evidence.' }
        const passport = await m3Api.passport('CCTNS_REPLICA', invStore.current?.purpose || 'Active Case Investigation').catch(() => null)
        return { kind: 'passport', data: passport }
      }
      case 'export': {
        const turns = chatStore.messages.map((m) => ({
          role: m.role, text: m.text || '', kind: m.kind || 'text', created_at: new Date().toISOString(),
        }))
        if (!iid) return { kind: 'text', text: 'Please start an investigation first.' }
        await m3Api.conversationPdf(iid, turns).catch(() => {})
        return { kind: 'text', text: 'Conversation PDF downloaded.' }
      }
      default: {
        if (!iid) return { kind: 'text', text: 'I can help you search cases, view trends, generate reports, and more. Try asking a specific question.' }
        const preview = await m3Api.preview(iid, text).catch(() => null)
        if (!preview) return { kind: 'text', text: 'Could not interpret that. Try rephrasing.' }
        return { kind: 'interpretation', preview }
      }
    }
  }, [chatStore, invStore])

  return { dispatch, classifyIntent }
}
