import { create } from 'zustand'

type FoundationState = {
  lastCheckedAt: string | null
  recordCheck: () => void
}

export const useFoundationStore = create<FoundationState>((set) => ({
  lastCheckedAt: null,
  recordCheck: () => set({ lastCheckedAt: new Date().toISOString() }),
}))
