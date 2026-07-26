import { useState } from 'react'
import { type ChatMessage } from '../../stores/chatStore'
import { useInvestigationStore } from '../../stores/investigationStore'
import { UserBubble, Assistant, Bubble, EngineBadge } from './ChatMessage'
import { MarkdownText } from './MarkdownText'
import {
  Case360Workspace,
  RelatedCasesPanel,
  FirRelationshipGraph,
  ShiftBriefingPanel,
  CrimeTrendsPanel,
  CaseComparePanel,
  VerificationPriorityPanel,
  BriefPreviewPanel,
  RecordAssurancePanel,
  QueryInterpretationPanel,
} from '../../features/m4/InvestigationExperience'
import { OffenceVisual, OffenceBadge } from '../OffenceVisual'
import { ConfidenceIndicator, ReasoningPanel, SourceCitations, HumanReviewBanner } from '../ExplainableAI'

const titleCase = (value: string) => value.replaceAll('_', ' ').toLowerCase()
const caseIdOf = (detail: any) => detail?.case?.id || detail?.overview?.id

function describeInterpretation(preview: any) {
  const plan = preview?.normalised_interpretation || {}
  const filters = plan.filters || {}
  const subject = filters.offence ? `for ${titleCase(String(filters.offence))} ` : ''
  const scope: string[] = []
  if (filters.location) scope.push(`near ${filters.location}`)
  if (filters.status) scope.push(String(filters.status).toLowerCase())
  if (filters.date_from || filters.date_to)
    scope.push(`between ${filters.date_from || 'the start'} and ${filters.date_to || 'now'}`)
  const action = plan.intent === 'DISCOVER' ? 'look for related and similar FIRs' : 'search FIR records'
  const scopeText = scope.length ? scope.join(', ') : 'across the selected sources'
  const confidence = Math.round((plan.confidence || 0) * 100)
  const sources = (plan.selected_sources || []).join(', ') || 'the selected sources'
  const engineBadge = preview.interpretation_engine === 'ai_assisted' ? 'AI-assisted' : 'deterministic'
  return {
    text: `I read this as: ${action} ${subject}${scopeText}. Confidence ${confidence}%. Confirm or edit below and I will query ${sources}.`,
    engine: engineBadge,
  }
}

const chipsFor = (preview: any) => {
  const filters = preview?.normalised_interpretation?.filters || {}
  return Object.entries(filters)
    .filter(([, value]) => value)
    .map(([key, value]) => `${titleCase(key)}: ${value}`)
}

type ChatMessagesProps = {
  messages: ChatMessage[]
  onRunSearch: (messageId: string, preview: any) => void
  onOpenCase: (caseId: string) => void
  onShowRelated: (caseId: string) => void
  onShowGraph: (caseId: string) => void
  onShowPriorities: (caseId: string) => void
  onShowAssurance: (caseId: string) => void
  onShowBrief: (caseId: string) => void
  onCompareCases: (baseId: string, rightId: string) => void
  onShowPath: (messageId: string, baseId: string, targetId: string) => void
  onResolveAssurance: (messageId: string, caseId: string, findingId: string, status: string) => void
  onOpenPassport: (id: string) => void
  onDownloadBrief: (caseId: string) => void
  onListen: (text: string) => void
  onToggleBookmark?: (messageId: string) => void
  isSupervisor: boolean
  isBusy: boolean
}

import { memo } from 'react'

export const ChatMessages = memo(function ChatMessages({
  messages,
  onRunSearch,
  onOpenCase,
  onShowRelated,
  onShowGraph,
  onShowPriorities,
  onShowAssurance,
  onShowBrief,
  onCompareCases,
  onShowPath,
  onResolveAssurance,
  onOpenPassport,
  onDownloadBrief,
  onListen,
  onToggleBookmark,
  isSupervisor,
  isBusy,
}: ChatMessagesProps) {
  return (
    <>
      {messages.map((message) => {
        if (message.role === 'user') {
          return <UserBubble key={message.id} text={message.text || ''} />
        }

        // Text message
        if (message.kind === 'text') {
          return (
            <Assistant key={message.id}>
              <Bubble>
                <MarkdownText content={message.text || ''} />
              </Bubble>
            </Assistant>
          )
        }

        // Interpretation message
        if (message.kind === 'interpretation' && message.preview) {
          const { text, engine } = describeInterpretation(message.preview)
          const chips = chipsFor(message.preview)
          return (
            <Assistant key={message.id}>
              <Bubble>
                <div className="flex flex-wrap items-start gap-2">
                  <p className="flex-1">{text}</p>
                  <EngineBadge engine={engine} />
                </div>
                {chips.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {chips.map((chip) => (
                      <span key={chip} className="rounded-full bg-teal-50 px-2 py-0.5 text-xs text-teal-900">
                        {chip}
                      </span>
                    ))}
                  </div>
                )}
              </Bubble>
              <details className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <summary className="cursor-pointer text-xs font-semibold text-slate-600">
                  Show / edit how I read this
                </summary>
                <div className="mt-3 space-y-3">
                  <QueryInterpretationPanel
                    preview={message.preview}
                    onChange={(preview) => {
                      // Update through store
                    }}
                  />
                </div>
              </details>
              {message.confirmed ? (
                <p className="animate-fade-in text-xs font-semibold text-teal-700">Searched ✓</p>
              ) : (
                <button
                  className="rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 hover:shadow-glow disabled:opacity-60 disabled:shadow-none"
                  disabled={isBusy}
                  onClick={() => onRunSearch(message.id, message.preview)}
                >
                  {isBusy ? 'Searching…' : 'Search records'}
                </button>
              )}
            </Assistant>
          )
        }

        // AI Answer message
        if (message.kind === 'answer' && message.answer) {
          const ai = message.answer
          return (
            <Assistant key={message.id}>
              <div
                className={`animate-scale-in rounded-2xl rounded-tl-sm border px-4 py-3 text-sm leading-relaxed shadow-bubble ${
                  ai.engine === 'ai_assisted'
                    ? 'border-purple-200 bg-gradient-to-br from-purple-50 to-white'
                    : 'border-slate-200 bg-white'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2 mb-1.5">
                  <EngineBadge engine={ai.engine || ai.model_used || 'ai_assisted'} />
                  {ai.confidence !== undefined && (
                    <ConfidenceIndicator score={ai.confidence} />
                  )}
                </div>

                <MarkdownText content={ai.answer} />

                {message.plan && (
                  <details className="mt-2.5 rounded-lg border border-slate-200/80 bg-slate-50/60 p-2.5 text-xs text-slate-600">
                    <summary className="cursor-pointer font-medium hover:text-teal-800">
                      🔍 Query Scope: {message.plan.intent} &middot; {Object.entries(message.plan.filters || {}).filter(([,v])=>v).map(([k,v]) => `${k}: ${v}`).join(', ') || 'All records'}
                    </summary>
                  </details>
                )}

                <SourceCitations sources={ai.cited_source_ids || []} onOpenPassport={onOpenPassport} />
                <ReasoningPanel reasoning={ai.reasoning} />
                <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-2">
                  <button
                    className="flex items-center gap-1 rounded-full border border-teal-300 bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-800 hover:bg-teal-100 disabled:opacity-50"
                    disabled={isBusy}
                    onClick={() => onListen(ai.answer)}
                    title="Read out text using Sarvam Bulbul v3 TTS"
                  >
                    <span>🎙️ Listen (Sarvam TTS)</span>
                  </button>
                  {onToggleBookmark && (
                    <button
                      className={`rounded-full border px-2.5 py-1 text-xs disabled:opacity-50 ${
                        message.bookmarked ? 'border-amber-300 bg-amber-50 text-amber-800 font-semibold' : 'border-slate-300 hover:border-amber-500'
                      }`}
                      onClick={() => onToggleBookmark(message.id)}
                    >
                      {message.bookmarked ? '🔖 Bookmarked' : '🔖 Bookmark'}
                    </button>
                  )}
                </div>
                {ai.grounded && <HumanReviewBanner />}
              </div>
            </Assistant>
          )
        }

        // Results message
        if (message.kind === 'results') {
          return (
            <Assistant key={message.id}>
              <div className="grid gap-2 sm:grid-cols-2">
                {message.results?.map((item: any, index: number) => (
                  <article
                    key={item.case_id || item.id}
                    style={{ animationDelay: `${Math.min(index * 60, 360)}ms` }}
                    className="animate-fade-in-up overflow-hidden rounded-xl border border-slate-200 bg-white shadow-bubble transition-all hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-panel"
                  >
                    <OffenceVisual offence={item.offence || item.category?.name || item.crime_major_head?.name} />
                    <div className="p-4">
                      <div className="flex items-start justify-between gap-2">
                        <b className="text-sm">{item.crime_number || item.fir_number || item.case_id}</b>
                        {item.masking?.applied && (
                          <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-900">Masked</span>
                        )}
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                        <OffenceBadge offence={item.offence || item.category?.name || item.crime_major_head?.name} />
                        <span className="text-xs text-slate-600">{item.canonical_status?.name || item.status || 'Status unavailable'}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.police_unit?.name || item.station_id || 'Unit unavailable'} · Registered {item.registered_at || '—'}
                      </p>
                      <button
                        className="mt-3 rounded-lg border border-teal-700 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-700 hover:text-white disabled:opacity-60"
                        disabled={isBusy}
                        onClick={() => onOpenCase(item.case_id || item.id)}
                      >
                        Open Case 360
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </Assistant>
          )
        }

        // Case 360 message
        if (message.kind === 'case' && message.detail) {
          return (
            <Assistant key={message.id}>
              <Case360Workspace detail={message.detail} onPassport={onOpenPassport} />
              <div className="flex flex-wrap gap-2">
                <button
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60"
                  disabled={isBusy}
                  onClick={() => onShowRelated(message.caseId!)}
                >
                  Related cases
                </button>
                <button
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60"
                  disabled={isBusy}
                  onClick={() => onShowGraph(message.caseId!)}
                >
                  Relationship graph
                </button>
                <button
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60"
                  disabled={isBusy}
                  onClick={() => onShowPriorities(message.caseId!)}
                >
                  Verification priorities
                </button>
                <button
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60"
                  disabled={isBusy}
                  onClick={() => onShowAssurance(message.caseId!)}
                >
                  Record assurance
                </button>
                <button
                  className="rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 disabled:opacity-60"
                  disabled={isBusy}
                  onClick={() => onShowBrief(message.caseId!)}
                >
                  Grounded brief
                </button>
              </div>
            </Assistant>
          )
        }

        // Panel-type messages
        if (message.kind === 'related' && message.data) {
          return (
            <Assistant key={message.id}>
              <RelatedCasesPanel
                data={message.data}
                onOpen={(id) => onOpenCase(id)}
                onCompare={(id) => onCompareCases(message.baseId!, id)}
              />
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'graph' && message.data) {
          return (
            <Assistant key={message.id}>
              <FirRelationshipGraph
                data={message.data}
                path={message.path}
                onOpen={(id) => onOpenCase(id)}
                onPath={(targetId) => onShowPath(message.id, message.baseId!, targetId)}
              />
              {message.data.edges?.length > 0 && (
                <details className="mt-2 rounded-lg border border-slate-200 bg-white">
                  <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900">
                    Edge details ({message.data.edges.length})
                  </summary>
                  <div className="space-y-1.5 border-t border-slate-100 px-3 py-2">
                    {message.data.edges.map((edge: any, i: number) => (
                      <div key={i} className="rounded-md bg-slate-50 p-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-slate-700">
                            {edge.source || edge.from} → {edge.target || edge.to}
                          </span>
                          <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-600">
                            {edge.relationship_type || edge.label || 'related'}
                          </span>
                        </div>
                        {edge.explanation && (
                          <p className="mt-1 text-slate-500">{edge.explanation}</p>
                        )}
                        {edge.metadata && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {Object.entries(edge.metadata).map(([k, v]) => (
                              <span key={k} className="rounded bg-white px-1 py-0.5 text-[9px] text-slate-500">
                                {k}: {String(v)}
                              </span>
                            ))}
                          </div>
                        )}
                        {edge.supporting_evidence?.length > 0 && (
                          <p className="mt-1 text-[10px] text-slate-400">
                            Evidence: {edge.supporting_evidence.map((e: any) => e.id || e).join(', ')}
                          </p>
                        )}
                        {edge.confidence !== undefined && (
                          <div className="mt-1.5">
                            <ConfidenceIndicator score={edge.confidence} label={`Edge confidence`} />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'priorities' && message.data) {
          return (
            <Assistant key={message.id}>
              <VerificationPriorityPanel data={message.data} />
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'compare' && message.data) {
          return (
            <Assistant key={message.id}>
              <CaseComparePanel data={message.data} />
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'briefing' && message.data) {
          return (
            <Assistant key={message.id}>
              <ShiftBriefingPanel data={message.data} />
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'trends' && message.data) {
          return (
            <Assistant key={message.id}>
              <CrimeTrendsPanel data={message.data} />
              <HumanReviewBanner />
            </Assistant>
          )
        }
        if (message.kind === 'brief' && message.data) {
          return (
            <div key={message.id}>
              <Assistant>
                <BriefPreviewPanel
                  data={message.data}
                  busy={isBusy}
                  onDownload={() => onDownloadBrief(message.caseId!)}
                />
                <div className="mt-3 space-y-2">
                  <ConfidenceIndicator score={1.0} label="Deterministic brief" />
                  {message.data.case_snapshot?.fir_number && (
                    <SourceCitations sources={[message.data.case_snapshot.fir_number]} onOpenPassport={onOpenPassport} />
                  )}
                  {message.data.human_review_required && <HumanReviewBanner variant="warning" />}
                </div>
              </Assistant>
            </div>
          )
        }
        if (message.kind === 'assurance' && message.data) {
          return (
            <Assistant key={message.id}>
              <RecordAssurancePanel
                data={message.data}
                canResolve={isSupervisor}
                onUpdate={(findingId, status) => onResolveAssurance(message.id, message.caseId!, findingId, status)}
              />
              <HumanReviewBanner />
            </Assistant>
          )
        }

        return null
      })}
    </>
  )
})
