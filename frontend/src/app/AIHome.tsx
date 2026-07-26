import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { useUIStore } from '../stores/uiStore'
import { ChatMessages } from '../components/chat/ChatMessages'
import { TypingIndicator } from '../components/chat/ChatMessage'
import { WelcomeScreen } from '../features/chat/WelcomeScreen'
import { Composer } from '../features/chat/Composer'
import { useChat } from '../hooks/useChat'
import { useVoice } from '../hooks/useVoice'
import { useFileUpload } from '../hooks/useFileUpload'
import { m3Api } from '../api/m3'
import { useInvestigationStore } from '../stores/investigationStore'
import { useEffect, useRef, useCallback } from 'react'
import { RightPanel } from './RightPanel'

export function AIHome() {
  const authStore = useAuthStore()
  const chatStore = useChatStore()
  const invStore = useInvestigationStore()
  const { intelligenceOpen } = useUIStore()
  const chat = useChat()
  const { files, addFiles } = useFileUpload()
  const isSupervisor = authStore.user?.role === 'SUPERVISOR'
  const bottomRef = useRef<HTMLDivElement>(null)

  const voice = useVoice(
    (v) => chatStore.setIsRecording(v),
    (text) => {
      const prev = useChatStore.getState().input
      chatStore.setInput(prev ? `${prev} ${text}` : text)
    },
  )

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatStore.messages.length, authStore.busy])

  const handleVoiceToggle = useCallback(() => {
    if (voice.isRecording) {
      voice.stopRecording()
    } else {
      voice.startBrowserSpeech('en-IN', (text) => {
        chatStore.setInput(text)
      })
    }
  }, [voice, chatStore])

  const handleListen = useCallback((text: string) => {
    voice.speakText(text, 'en-IN')
  }, [voice])

  const handleNewTopic = useCallback(() => {
    chat.reset()
  }, [chat])

  const handleToggleBookmark = useCallback((messageId: string) => {
    chatStore.toggleBookmark(messageId)
  }, [chatStore])

  const handleDownloadBrief = useCallback(async (caseId: string) => {
    const inv = invStore.current; if (!inv) return
    await m3Api.briefPdf(inv.id, caseId)
  }, [invStore.current?.id])

  const handleFileDrop = useCallback(async (droppedFiles: File[]) => {
    await addFiles(droppedFiles, invStore.current?.id)
  }, [addFiles, invStore.current?.id])

  const handleSend = useCallback(async (text: string) => {
    if (!text.trim()) return
    chat.sendMessage(text)
  }, [chat])

  // Persist session when first message arrives
  const saveSessionRef = useRef(false)
  useEffect(() => {
    if (saveSessionRef.current) { saveSessionRef.current = false; return }
    if (chatStore.messages.length > 0 && authStore.user && !chatStore.currentSessionId) {
      const session = {
        id: Math.random().toString(36).slice(2),
        title: chatStore.conversationTitle || 'Untitled Investigation',
        messages: chatStore.messages,
        tags: [], bookmarked: false, archived: false, pinned: false,
        investigationId: invStore.current?.id || null,
        caseId: chatStore.activeCaseId,
        createdAt: Date.now(), updatedAt: Date.now(),
        messageCount: chatStore.messages.length,
      }
      chatStore.setCurrentSessionId(session.id)
      chatStore.addSession(session)
    }
  }, [chatStore.messages.length === 1, authStore.user])

  const showWelcome = chatStore.messages.length === 0

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* ── Main chat area ── */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Error banner */}
        {authStore.error && (
          <div className="mx-4 mt-2 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300 animate-fade-in">
            <span>{authStore.error}</span>
            <button
              onClick={() => authStore.clearError()}
              className="ml-3 font-semibold hover:text-red-600"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Messages / welcome */}
        <div className="flex-1 overflow-y-auto">
          {showWelcome ? (
            <div className="flex min-h-full flex-col justify-center">
              <WelcomeScreen onPromptClick={(text) => {
                chatStore.setInput(text)
                chat.sendMessage(text)
              }} />
            </div>
          ) : (
            <div className="mx-auto w-full max-w-3xl px-4 py-6">
              <ChatMessages
                messages={chatStore.messages}
                onRunSearch={(msgId, preview) => chat.runSearch(msgId, preview)}
                onOpenCase={(caseId) => chat.openCase(caseId)}
                onShowRelated={async (caseId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.related(inv.id, caseId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'related', data, caseId, baseId: caseId, timestamp: Date.now() })
                }}
                onShowGraph={async (caseId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.firGraph(inv.id, caseId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'graph', data, caseId, baseId: caseId, timestamp: Date.now() })
                }}
                onShowPriorities={async (caseId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.priorities(inv.id, caseId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'priorities', data, caseId, timestamp: Date.now() })
                }}
                onShowAssurance={async (caseId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.firAssurance(inv.id, caseId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'assurance', data, caseId, timestamp: Date.now() })
                }}
                onShowBrief={async (caseId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.brief(inv.id, caseId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'brief', data, caseId, timestamp: Date.now() })
                }}
                onCompareCases={async (baseId, rightId) => {
                  const inv = invStore.current; if (!inv) return
                  const data = await m3Api.compare(inv.id, baseId, rightId).catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'compare', data, timestamp: Date.now() })
                }}
                onShowPath={() => {}}
                onResolveAssurance={async (messageId, caseId, findingId, status) => {
                  const inv = invStore.current; if (!inv) return
                  await m3Api.updateFirAssurance(inv.id, caseId, findingId, { status }).catch(() => {})
                }}
                onOpenPassport={async (id) => {
                  const data = await m3Api.passport(id, invStore.current?.purpose || 'Active Case Investigation').catch(() => null)
                  if (data) chatStore.addMessage({ id: Math.random().toString(36).slice(2), role: 'assistant', kind: 'passport', data, timestamp: Date.now() })
                }}
                onDownloadBrief={handleDownloadBrief}
                onListen={handleListen}
                onToggleBookmark={handleToggleBookmark}
                isSupervisor={isSupervisor}
                isBusy={Boolean(authStore.busy)}
              />
              {authStore.busy && <TypingIndicator />}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* ── Composer (always visible at bottom) ── */}
        <div className="border-t border-slate-200/60 bg-white px-4 py-3 dark:border-slate-800/60 dark:bg-[#0f0f0f]">
          <div className="mx-auto w-full max-w-3xl">
            <Composer
              input={chatStore.input}
              onInputChange={chatStore.setInput}
              onSend={handleSend}
              onVoiceToggle={handleVoiceToggle}
              isRecording={voice.isRecording || chatStore.isRecording}
              isBusy={Boolean(authStore.busy)}
              onNewTopic={handleNewTopic}
              onFileDrop={handleFileDrop}
            />
            <p className="mt-2 text-center text-[10px] text-slate-400 dark:text-slate-600">
              ANVAYA AI can make mistakes. Human review required for all operational decisions.
            </p>
          </div>
        </div>
      </div>

      {/* ── Intelligence panel (right) ── */}
      {intelligenceOpen && (
        <div className="hidden lg:block">
          <RightPanel />
        </div>
      )}
    </div>
  )
}
