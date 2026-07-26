import { create } from 'zustand'
import type { User } from '../api/m3'

type AuthState = {
  user: User | null
  busy: string
  error: string
  setUser: (user: User | null) => void
  setBusy: (label: string) => void
  setError: (error: string) => void
  clearError: () => void
  isAuthenticated: () => boolean
  isSupervisor: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  busy: '',
  error: '',
  setUser: (user) => set({ user }),
  setBusy: (busy) => set({ busy }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: '' }),
  isAuthenticated: () => get().user !== null,
  isSupervisor: () => get().user?.role === 'SUPERVISOR',
}))
