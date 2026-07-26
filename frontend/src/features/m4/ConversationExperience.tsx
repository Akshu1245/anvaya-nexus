import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { m3Api, type HealthStatus, type Source } from '../../api/m3'
import { JourneyStepper } from '../../components/ui'
import { SourcePassportDrawer } from './SourcePassportDrawer'
import { LoginLanding } from './InvestigationExperience'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore, type ConversationSession } from '../../stores/chatStore'
import { useInvestigationStore } from '../../stores/investigationStore'
import { useChat } from '../../hooks/useChat'
import { useVoice } from '../../hooks/useVoice'
import { ChatComposer, ChatEmptyState, ChatMessages, ChatCoach, ChatHelp, TypingIndicator } from '../../components/chat'
import { InvestigationTimeline } from '../../components/InvestigationTimeline'
import { VoiceTranscript, MixedLanguageIndicator } from '../../components/VoiceTranscript'
import { useKeyboardShortcuts, useCommandPalette, ShortcutGuide } from '../../components/UXPolish'
import { ShiftIntelligence } from '../../components/ShiftIntelligence'
import { CopilotPanel } from '../../components/Copilot'

const LANGUAGES = [
  { code: 'en-IN', label: 'English', sarvamCode: 'en-IN' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ', sarvamCode: 'kn-IN' },
  { code: 'hi-IN', label: 'हिन्दी', sarvamCode: 'hi-IN' },
]

const RETRY_LABELS: Record<string, string> = {
  briefing: 'Preparing shift briefing',
  trends: 'Loading crime trends',
  'network-clusters': 'Resolving network clusters',
  'conversation-pdf': 'Exporting conversation PDF',
  'brief-pdf': 'Generating PDF',
  search: 'Searching records',
  case: 'Opening Case 360',
  'brief': 'Preparing dossier',
}

const examples = [
  'Find unresolved chain snatching at SYN-STN-01',
  'ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ ಜಯನಗರ ತೋರಿಸಿ',
  'Show my shift briefing',
  'Show recorded crime trends',
  'Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.',
]

const uid = () => Math.random().toString(36).slice(2)

export function ConversationExperience() {
  const authStore = useAuthStore()
  const chatStore = useChatStore()
  const invStore = useInvestigationStore()

  const [username, setUsername] = useState('investigator.demo')
  const [password, setPassword] = useState('')
  const [language, setLanguage] = useState(LANGUAGES[0])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [home, setHome] = useState<any>(null)
  const [control, setControl] = useState<any>(null)
  const [showSources, setShowSources] = useState(false)
  const [passport, setPassport] = useState<any>(null)
  const [selected, setSelected] = useState<string[]>(['CCTNS_REPLICA'])
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [shiftData, setShiftData] = useState<any>(null)
  const [copilotData, setCopilotData] = useState<any>(null)
  const [showShiftIntel, setShowShiftIntel] = useState(false)
  const [showCopilot, setShowCopilot] = useState(false)

  const lastBusyRef = useRef('')
  if (authStore.busy) lastBusyRef.current = authStore.busy

  const chat = useChat()
  const voice = useVoice(
    (v) => chatStore.setIsRecording(v),
    (text) => {
      const prev = useChatStore.getState().input
      chatStore.setInput(prev ? `${prev} ${text}` : text)
    },
  )

  const voiceAvailable = voice.isVoiceAvailable(health)

  // Save conversation as session when messages change
  // Save conversation progress (not via effect to avoid loops; called from sendMessage)
  const saveSessionRef = useRef(false)
  useEffect(() => {
    if (saveSessionRef.current) {
      saveSessionRef.current = false
      return
    }
    if (chatStore.messages.length > 0 && authStore.user && !chatStore.currentSessionId) {
      const session: ConversationSession = {
        id: uid(),
        title: chatStore.conversationTitle || 'Untitled Investigation',
        messages: chatStore.messages,
        tags: [],
        bookmarked: false,
        archived: false,
        pinned: false,
        investigationId: invStore.current?.id || null,
        caseId: chatStore.activeCaseId,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messageCount: chatStore.messages.length,
      }
      chatStore.setCurrentSessionId(session.id)
      chatStore.addSession(session)
    }
  }, [chatStore.messages.length === 1])

  // Load shift intelligence
  const loadShiftIntel = useCallback(async () => {
    const { user } = useAuthStore.getState()
    if (!user?.assigned_station) return
    const { setBusy, setShiftChanges } = {
      setBusy: useAuthStore.getState().setBusy,
      setShiftChanges: useInvestigationStore.getState().setShiftChanges,
    }
    setBusy('shift')
    try {
      const data = await m3Api.shiftIntelligence(user.assigned_station)
      if (data) {
        setShiftData(data)
        setShiftChanges(data)
      }
    } catch {
      /* noop */
    } finally {
      setBusy('')
    }
  }, [])

  const isLoggedIn = Boolean(authStore.user)
  useEffect(() => {
    if (isLoggedIn) {
      loadShiftIntel()
    }
  }, [isLoggedIn, loadShiftIntel])

  const loadCopilot = useCallback(async (caseId: string) => {
    const inv = useInvestigationStore.getState().current
    if (!inv) return
    const auth = useAuthStore.getState()
    auth.setBusy('copilot')
    try {
      const data = await m3Api.copilotAnalyze(inv.id, caseId)
      if (data) {
        useInvestigationStore.getState().setCopilot(data)
        setCopilotData(data)
      }
    } catch {
      /* noop */
    } finally {
      auth.setBusy('')
    }
  }, [])

  // Listen for copilot actions from IntelligencePanel
  useEffect(() => {
    const handler = (e: CustomEvent) => {
      const { action, payload } = e.detail
      if (action === 'suggestion' && payload?.case_id) {
        chat.openCase(payload.case_id)
      }
    }
    window.addEventListener('copilot-action' as any, handler as any)
    return () => window.removeEventListener('copilot-action' as any, handler as any)
  }, [chat])

  useEffect(() => {
    m3Api.health()
      .then(setHealth)
      .catch(() => setHealth({ status: 'ok', service: 'anvaya-api', environment: 'unknown', database: 'ok', public_demo_enabled: false, ai_assist_enabled: false, voice_enabled: false }))
  }, [])

  const load = useCallback(async () => {
    const [nextHome, nextControl] = await Promise.all([
      m3Api.home().catch(() => null),
      m3Api.sourceControl('Active Case Investigation').catch(() => ({ sources: [] })),
    ])
    setHome(nextHome)
    setControl(nextControl)
  }, [])

  const login = useCallback(async () => {
    authStore.setBusy('login')
    try {
      const u = await m3Api.login(username, password)
      if (u) { authStore.setUser(u); await load() }
    } catch (e) { authStore.setError((e as Error).message) } finally { authStore.setBusy('') }
  }, [username, password, authStore, load])

  const publicDemo = useCallback(async () => {
    authStore.setBusy('public-demo')
    try {
      const u = await m3Api.publicDemo()
      if (u) { authStore.setUser(u); await load() }
    } catch (e) { authStore.setError((e as Error).message) } finally { authStore.setBusy('') }
  }, [authStore, load])

  const resetConversation = useCallback(() => {
    chat.reset()
    setSelected(['CCTNS_REPLICA'])
    setCopilotData(null)
    setShiftData(null)
  }, [chat])

  const handleLogout = useCallback(async () => {
    try { await m3Api.logout() } catch { /* noop */ }
    authStore.setUser(null)
    resetConversation()
  }, [authStore, resetConversation])

  const toggleSource = useCallback(async (id: string, on: boolean) => {
    const next = on ? [...selected, id] : selected.filter((s) => s !== id)
    setSelected(next)
    if (invStore.current) {
      authStore.setBusy('sources')
      try {
        const updated = await m3Api.updateSources(invStore.current.id, next)
        if (updated) invStore.setCurrent(updated)
      } catch (e) { authStore.setError((e as Error).message) } finally { authStore.setBusy('') }
    }
  }, [selected, invStore, authStore])

  const openPassport = useCallback((id: string) => {
    authStore.setBusy('passport')
    m3Api.passport(id, 'Active Case Investigation')
      .then((v) => v && setPassport(v))
      .catch(() => authStore.setError('Could not load source passport.'))
      .finally(() => authStore.setBusy(''))
  }, [authStore])

  const handleMic = useCallback(() => {
    if (chatStore.isRecording || voice.isRecording) {
      voice.stopRecording()
      return
    }
    if (health?.voice_enabled) {
      voice.startRecording(language.sarvamCode)
      return
    }
    voice.startBrowserSpeech(language.code, (text) => {
      const prev = useChatStore.getState().input
      chatStore.setInput(prev ? `${prev} ${text}` : text)
    })
  }, [health, voice, language, chatStore])

  const handleListen = useCallback((text: string) => {
    voice.speakText(text, language.sarvamCode)
  }, [voice, language])

  const handleRunSearch = useCallback((messageId: string, preview: any) => {
    chat.runSearch(messageId, preview)
  }, [chat])

  // Keyboard shortcuts
  const shortcuts = useMemo(() => [
    { key: 'n', ctrl: true, label: 'New conversation', action: resetConversation },
    { key: 'b', ctrl: true, label: 'Toggle sidebar', action: () => useChatStore.getState().setInput('') },
    { key: 'i', ctrl: true, label: 'Toggle intelligence', action: () => {} },
    { key: '/', label: 'Focus search', action: () => document.querySelector<HTMLTextAreaElement>('[data-composer]')?.focus() },
    { key: 'Escape', label: 'Close panels', action: () => { setShowShortcuts(false); setShowShiftIntel(false); setShowCopilot(false) } },
  ], [resetConversation])
  useKeyboardShortcuts(shortcuts)

  // Command palette
  const commands = [
    { id: 'new-chat', label: 'New conversation', icon: '💬', category: 'Conversation', action: resetConversation },
    { id: 'shift-intel', label: 'Show shift intelligence', icon: '📋', category: 'Investigation', action: () => loadShiftIntel().then(() => setShowShiftIntel(true)) },
    { id: 'copilot', label: 'Open investigation copilot', icon: '🤖', category: 'Investigation', action: () => setShowCopilot(true) },
    { id: 'export-pdf', label: 'Export conversation as PDF', icon: '📄', category: 'Export', action: () => chat.exportPdf() },
    { id: 'help', label: 'Open help', icon: '❓', category: 'General', action: () => chatStore.setHelpOpen(true) },
    { id: 'shortcuts', label: 'Show keyboard shortcuts', icon: '⌨️', category: 'General', action: () => setShowShortcuts(true) },
  ]

  const { palette: commandPalette } = useCommandPalette(commands)

  if (!authStore.user) {
    return <LoginLanding username={username} password={password} busy={authStore.busy} error={authStore.error} health={health} onSelect={setUsername} onPassword={setPassword} onLogin={login} onPublicDemo={publicDemo} />
  }

  return (
    <section aria-label="Conversational investigation" className="flex min-h-[70vh] flex-col gap-4">
      <header className="animate-fade-in rounded-2xl bg-gradient-to-br from-navy-950 via-navy-900 to-teal-900 p-5 text-white shadow-panel">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-teal-300">{authStore.user.role}</p>
            <h2 className="text-xl font-semibold">ANVAYA · Chat with your case data</h2>
            <p className="text-xs text-teal-100/80">{authStore.user.assigned_station || 'Pattern scope'} · {authStore.user.assigned_district || '—'}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-lg border border-white/20 bg-white/10 p-0.5" role="group" aria-label="Language">
              {LANGUAGES.map((lang) => (
                <button key={lang.code} type="button" onClick={() => setLanguage(lang)}
                  className={`rounded-md px-2 py-1 text-xs font-semibold transition-colors ${language.code === lang.code ? 'bg-teal-600 text-white' : 'text-white/70 hover:text-white'}`}>
                  {lang.label}
                </button>
              ))}
            </div>
            <button type="button" className="rounded-lg border border-white/30 px-3 py-1.5 text-xs disabled:opacity-60" disabled={Boolean(authStore.busy)} onClick={resetConversation}>New chat</button>
            <button type="button" className="rounded-lg border border-white/30 px-3 py-1.5 text-xs disabled:opacity-60" disabled={Boolean(authStore.busy)} onClick={handleLogout}>Logout</button>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {health?.ai_assist_enabled && <span className="animate-scale-in rounded-full bg-purple-500/20 px-3 py-0.5 text-xs font-semibold text-purple-200 ring-1 ring-purple-400/40">✦ AI Assist ON</span>}
          {health?.voice_enabled && <span className="animate-scale-in rounded-full bg-teal-500/20 px-3 py-0.5 text-xs font-semibold text-teal-200 ring-1 ring-teal-400/40">Sarvam Voice ON</span>}
          <button type="button" onClick={() => setShowCopilot(!showCopilot)} className="rounded-full bg-white/10 px-3 py-0.5 text-xs hover:bg-white/20">
            {showCopilot ? 'Hide Copilot' : '🤖 Copilot'}
          </button>
          <button type="button" onClick={() => loadShiftIntel().then(() => setShowShiftIntel(true))} className="rounded-full bg-white/10 px-3 py-0.5 text-xs hover:bg-white/20">
            📋 Shift Intel
          </button>
          <button type="button" onClick={() => setShowShortcuts(true)} className="rounded-full bg-white/10 px-3 py-0.5 text-xs hover:bg-white/20">
            ⌨️ Shortcuts
          </button>
        </div>
        <details className="mt-3 rounded-lg bg-white/5 p-3" open={showSources} onToggle={(e) => setShowSources((e.target as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer text-xs font-semibold text-teal-200">Sources · {selected.length} selected</summary>
          <div className="mt-2 flex flex-wrap gap-2">
            {control?.sources?.filter((s: Source) => s.selectable).map((s: Source) => (
              <label key={s.id} className="rounded border border-white/20 px-2 py-1 text-xs">
                <input type="checkbox" checked={selected.includes(s.id)} onChange={(e) => toggleSource(s.id, e.target.checked)} /> {s.name}
              </label>
            ))}
          </div>
        </details>
        {home?.degraded_mode && <p className="mt-3 rounded bg-amber-200 p-2 text-xs text-amber-950">Degraded sources: {home.degraded_sources?.join(', ')}.</p>}
      </header>

      {/* Shift Intelligence Panel */}
      {showShiftIntel && (
        <div className="animate-fade-in-up rounded-2xl border border-slate-200 bg-white shadow-panel">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-slate-800">Shift Intelligence</h3>
            <button type="button" onClick={() => setShowShiftIntel(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            <ShiftIntelligence data={shiftData} />
          </div>
        </div>
      )}

      {/* Copilot Panel */}
      {showCopilot && (
        <div className="animate-fade-in-up rounded-2xl border border-slate-200 bg-white shadow-panel">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-slate-800">Investigation Copilot</h3>
            <button type="button" onClick={() => setShowCopilot(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto">
            <CopilotPanel data={copilotData} onAction={(action, payload) => {
              if (payload?.case_id) chat.openCase(payload.case_id)
            }} />
          </div>
        </div>
      )}

      <div className="flex gap-4">
        <div className="flex-1 space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-bubble">
            <JourneyStepper current={chat.stage} maxReached={chat.maxStage} onSelect={chat.advanceStage} />
          </div>

          <div className="flex-1 space-y-4">
            {chat.messages.length === 0 && (
              <ChatEmptyState examples={examples} ask={chat.sendMessage} aiAssistEnabled={health?.ai_assist_enabled} />
            )}
            <ChatMessages
              messages={chat.messages}
              onRunSearch={handleRunSearch}
              onOpenCase={(id) => {
                chat.openCase(id)
                loadCopilot(id)
              }}
              onShowRelated={(id) => {
                authStore.setBusy('related')
                if (invStore.current) m3Api.related(invStore.current.id, id)
                  .then((d) => d && chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'related', data: d, baseId: id }))
                  .catch((e) => authStore.setError(e.message))
                  .finally(() => authStore.setBusy(''))
              }}
              onShowGraph={(id) => {
                authStore.setBusy('graph')
                if (invStore.current) m3Api.firGraph(invStore.current.id, id)
                  .then((d) => d && chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'graph', data: d, baseId: id, path: null }))
                  .catch((e) => authStore.setError(e.message))
                  .finally(() => authStore.setBusy(''))
              }}
              onShowPriorities={(id) => {
                authStore.setBusy('priorities')
                if (invStore.current) m3Api.priorities(invStore.current.id, id)
                  .then((d) => { if (d) { chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'priorities', data: d }); chat.advanceStage('PRIORITISE') } })
                  .catch((e) => authStore.setError(e.message))
                  .finally(() => authStore.setBusy(''))
              }}
              onShowAssurance={(id) => {
                authStore.setBusy('assurance')
                if (invStore.current) m3Api.firAssurance(invStore.current.id, id)
                  .then((d) => d && chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'assurance', data: d, caseId: id }))
                  .catch((e) => authStore.setError(e.message))
                  .finally(() => authStore.setBusy(''))
              }}
              onShowBrief={(id) => {
                authStore.setBusy('brief')
                if (invStore.current) m3Api.brief(invStore.current.id, id)
                  .then((d) => { if (d) { chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'brief', data: d, caseId: id }); chat.advanceStage('REPORT') } })
                  .catch((e) => authStore.setError(e.message))
                  .finally(() => authStore.setBusy(''))
              }}
              onCompareCases={(baseId, rightId) => {
                if (invStore.current) m3Api.compare(invStore.current.id, baseId, rightId)
                  .then((d) => d && chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'compare', data: d }))
                  .catch((e) => authStore.setError(e.message))
              }}
              onShowPath={(messageId, baseId, targetId) => {
                if (invStore.current) m3Api.firGraphPath(invStore.current.id, baseId, targetId)
                  .then((d) => d && chat.updateMessage(messageId, { path: d }))
                  .catch(() => {})
              }}
              onResolveAssurance={async (messageId, caseId, findingId, status) => {
                if (!invStore.current) return
                try {
                  await m3Api.updateFirAssurance(invStore.current.id, caseId, findingId, { status })
                  const data = await m3Api.firAssurance(invStore.current.id, caseId)
                  if (data) chat.updateMessage(messageId, { data })
                } catch (e) { authStore.setError((e as Error).message) }
              }}
              onOpenPassport={openPassport}
              onDownloadBrief={(caseId) => {
                if (invStore.current) {
                  authStore.setBusy('brief-pdf')
                  m3Api.briefPdf(invStore.current.id, caseId).finally(() => authStore.setBusy(''))
                }
              }}
              onListen={handleListen}
              onToggleBookmark={(messageId) => chatStore.toggleBookmark(messageId)}
              isSupervisor={authStore.user?.role === 'SUPERVISOR'}
              isBusy={Boolean(authStore.busy)}
            />
            {authStore.busy && <TypingIndicator />}
            <div ref={chat.bottomRef} />
          </div>

          {chatStore.pendingTranscript && (
            <VoiceTranscript text={chatStore.pendingTranscript} language={language.label} isFinal />
          )}

          <ChatComposer
            input={chatStore.input}
            onInputChange={chatStore.setInput}
            onSend={() => chat.sendMessage()}
            onVoiceToggle={handleMic}
            isRecording={chatStore.isRecording}
            isVoiceAvailable={voiceAvailable}
            isBusy={Boolean(authStore.busy)}
            parentMessageId={chatStore.parentMessageId}
            onNewTopic={() => chatStore.setParentMessageId('')}
            placeholder={`Ask in ${language.label} or code-mixed — e.g. unresolved chain snatching near Jayanagar`}
          />
        </div>
        <div className="hidden w-64 shrink-0 xl:block">
          <InvestigationTimeline />
        </div>
      </div>

      {passport && <SourcePassportDrawer passport={passport} onClose={() => setPassport(null)} />}
      {authStore.error && (
        <div role="alert" className="animate-fade-in-up flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 shadow-sm">
          <span>{authStore.error}</span>
          <div className="flex items-center gap-2">
            {lastBusyRef.current && RETRY_LABELS[lastBusyRef.current] && (
              <button type="button" onClick={() => { const q = lastBusyRef.current; authStore.clearError(); lastBusyRef.current = ''; chat.sendMessage(q === 'briefing' ? 'Show my shift briefing' : q === 'trends' ? 'Show recorded crime trends' : q) }} className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-bold hover:bg-red-100">
                Retry {RETRY_LABELS[lastBusyRef.current]}
              </button>
            )}
            <button type="button" onClick={authStore.clearError} className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-bold hover:bg-red-100">Dismiss</button>
          </div>
        </div>
      )}

      {/* Keyboard shortcuts modal */}
      {showShortcuts && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setShowShortcuts(false)} />
          <div className="relative z-10 w-full max-w-sm animate-fade-in-up rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
            <h3 className="mb-3 text-sm font-bold text-slate-800">Keyboard Shortcuts</h3>
            <ShortcutGuide />
            <button type="button" onClick={() => setShowShortcuts(false)} className="mt-4 w-full rounded-lg bg-slate-100 py-2 text-xs font-medium text-slate-700 hover:bg-slate-200">
              Close
            </button>
          </div>
        </div>
      )}

      {commandPalette}

      <ChatHelp
        open={chatStore.helpOpen}
        onClose={() => chatStore.setHelpOpen(false)}
        onAsk={(text) => { chatStore.setHelpOpen(false); chat.sendMessage(text) }}
        onStartGuidedDemo={() => {
          chatStore.setHelpOpen(false)
          chatStore.setInput('Find unresolved chain snatching at SYN-STN-01')
          chat.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'text', text: 'Guided demo: send the prepared synthetic query. I will show my interpretation first.' })
        }}
        onExportPdf={() => { chatStore.setHelpOpen(false); chat.exportPdf() }}
      />

      <ChatCoach
        step={chatStore.coachStep}
        onNext={() => chatStore.setCoachStep(chatStore.coachStep + 1)}
        onDismiss={chat.dismissCoach}
      />
    </section>
  )
}
