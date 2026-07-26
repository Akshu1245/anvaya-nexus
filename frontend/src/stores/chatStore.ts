import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  kind: string
  text?: string
  preview?: any
  detail?: any
  data?: any
  results?: any[]
  answer?: any
  caseId?: string
  baseId?: string
  plan?: any
  path?: any
  confirmed?: boolean
  pinned?: boolean
  bookmarked?: boolean
  tags?: string[]
  timestamp?: number
}

export type ConversationSession = {
  id: string
  title: string
  messages: ChatMessage[]
  tags: string[]
  bookmarked: boolean
  archived: boolean
  pinned: boolean
  investigationId: string | null
  caseId: string | null
  createdAt: number
  updatedAt: number
  messageCount: number
  folderId?: string | null
}

export type ConversationFolder = {
  id: string
  name: string
  icon?: string
  createdAt: number
}

type ChatState = {
  messages: ChatMessage[]
  input: string
  parentMessageId: string
  activeCaseId: string | null
  isRecording: boolean
  pendingTranscript: string
  stage: 'ASK' | 'DISCOVER' | 'VERIFY' | 'PRIORITISE' | 'REPORT'
  maxStage: 'ASK' | 'DISCOVER' | 'VERIFY' | 'PRIORITISE' | 'REPORT'
  helpOpen: boolean
  coachStep: number
  conversationTitle: string
  sessions: ConversationSession[]
  currentSessionId: string
  sessionSearch: string
  folders: ConversationFolder[]
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void
  setInput: (input: string) => void
  setParentMessageId: (id: string) => void
  setActiveCaseId: (id: string | null) => void
  setIsRecording: (recording: boolean) => void
  setPendingTranscript: (text: string) => void
  setStage: (stage: ChatState['stage']) => void
  setMaxStage: (stage: ChatState['maxStage']) => void
  advanceStage: (next: ChatState['stage']) => void
  setHelpOpen: (open: boolean) => void
  setCoachStep: (step: number) => void
  setConversationTitle: (title: string) => void
  reset: () => void
  addSession: (session: ConversationSession) => void
  removeSession: (id: string) => void
  renameSession: (id: string, title: string) => void
  archiveSession: (id: string) => void
  pinSession: (id: string) => void
  toggleBookmark: (messageId: string) => void
  togglePin: (messageId: string) => void
  addTag: (messageId: string, tag: string) => void
  removeTag: (messageId: string, tag: string) => void
  setCurrentSessionId: (id: string) => void
  setSessionSearch: (query: string) => void
  setSessions: (sessions: ConversationSession[]) => void
  restoreSession: (id: string) => void
  createFolder: (name: string) => string
  renameFolder: (id: string, name: string) => void
  deleteFolder: (id: string) => void
  moveSessionToFolder: (sessionId: string, folderId: string | null) => void
}

const stageOrder: Array<ChatState['stage']> = ['ASK', 'DISCOVER', 'VERIFY', 'PRIORITISE', 'REPORT']

const uid = () => Math.random().toString(36).slice(2)

const initial = {
  messages: [],
  input: '',
  parentMessageId: '',
  activeCaseId: null,
  isRecording: false,
  pendingTranscript: '',
  stage: 'ASK' as ChatState['stage'],
  maxStage: 'REPORT' as ChatState['stage'],
  helpOpen: false,
  coachStep: (() => {
    try {
      return localStorage.getItem('anvaya_coach_v1') ? -1 : 0
    } catch {
      return 0
    }
  })(),
  conversationTitle: 'New Investigation',
  sessions: [] as ConversationSession[],
  currentSessionId: '',
  sessionSearch: '',
  folders: [],
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
  ...initial,
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => {
      const newMsg = { ...message, timestamp: Date.now() }
      const newMessages = [...state.messages, newMsg]
      // Auto-save current messages into the active session
      if (state.currentSessionId) {
        const updatedSessions = state.sessions.map((s) =>
          s.id === state.currentSessionId
            ? { ...s, messages: newMessages, messageCount: newMessages.length, updatedAt: Date.now() }
            : s
        )
        return { messages: newMessages, sessions: updatedSessions }
      }
      return { messages: newMessages }
    }),
  updateMessage: (id, patch) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    })),
  setInput: (input) => set({ input }),
  setParentMessageId: (id) => set({ parentMessageId: id }),
  setActiveCaseId: (id) => set({ activeCaseId: id }),
  setIsRecording: (isRecording) => set({ isRecording }),
  setPendingTranscript: (text) => set({ pendingTranscript: text }),
  setStage: (stage) => set({ stage }),
  setMaxStage: (maxStage) => set({ maxStage }),
  advanceStage: (next) => {
    const currentMax = stageOrder.indexOf(get().maxStage)
    const nextIdx = stageOrder.indexOf(next)
    set({
      stage: next,
      maxStage: nextIdx > currentMax ? next : get().maxStage,
    })
  },
  setHelpOpen: (helpOpen) => set({ helpOpen }),
  setCoachStep: (coachStep) => set({ coachStep }),
  setConversationTitle: (conversationTitle) => set({ conversationTitle }),
  reset: () =>
    set({
      ...initial,
      coachStep: get().coachStep,
      currentSessionId: get().currentSessionId,
      sessions: get().sessions,
    }),
  addSession: (session) =>
    set((state) => ({ sessions: [session, ...state.sessions] })),
  removeSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      currentSessionId: state.currentSessionId === id ? '' : state.currentSessionId,
    })),
  renameSession: (id, title) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, title, updatedAt: Date.now() } : s
      ),
    })),
  archiveSession: (id) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, archived: !s.archived, updatedAt: Date.now() } : s
      ),
    })),
  pinSession: (id) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, pinned: !s.pinned, updatedAt: Date.now() } : s
      ),
    })),
  toggleBookmark: (messageId) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, bookmarked: !m.bookmarked } : m
      ),
    })),
  togglePin: (messageId) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId ? { ...m, pinned: !m.pinned } : m
      ),
    })),
  addTag: (messageId, tag) =>
    set((state) => ({
      messages: state.messages.map((m) => {
        if (m.id !== messageId) return m
        const tags = (m as any).tags || []
        return { ...m, tags: tags.includes(tag) ? tags : [...tags, tag] }
      }),
    })),
  removeTag: (messageId, tag) =>
    set((state) => ({
      messages: state.messages.map((m) => {
        if (m.id !== messageId) return m
        const tags = (m as any).tags || []
        return { ...m, tags: tags.filter((t: string) => t !== tag) }
      }),
    })),
  setCurrentSessionId: (id) => set({ currentSessionId: id }),
  setSessionSearch: (query) => set({ sessionSearch: query }),
  setSessions: (sessions) => set({ sessions }),
  restoreSession: (id) => {
    const session = get().sessions.find((s) => s.id === id)
    if (!session) return
    set({
      currentSessionId: id,
      messages: session.messages,
      conversationTitle: session.title,
      activeCaseId: session.caseId,
    })
  },
  createFolder: (name) => {
    const id = uid()
    const folder: ConversationFolder = { id, name, createdAt: Date.now() }
    set((state) => ({ folders: [...state.folders, folder] }))
    return id
  },
  renameFolder: (id, name) =>
    set((state) => ({
      folders: state.folders.map((f) => (f.id === id ? { ...f, name } : f)),
    })),
  deleteFolder: (id) =>
    set((state) => ({
      folders: state.folders.filter((f) => f.id !== id),
      sessions: state.sessions.map((s) =>
        s.folderId === id ? { ...s, folderId: null } : s
      ),
    })),
  moveSessionToFolder: (sessionId, folderId) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === sessionId ? { ...s, folderId } : s
      ),
    })),
    }),
    {
      name: 'anvaya-chat-v2',
      partialize: (state) => ({
        sessions: state.sessions,
        folders: state.folders,
        currentSessionId: state.currentSessionId,
        coachStep: state.coachStep,
      }),
    }
  )
)

