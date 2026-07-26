import { create } from 'zustand'

export type PortalSection = 'search' | 'briefing' | 'trends' | 'chat' | 'about' | 'helplines' | 'privacy' | 'screen-reader'
export type SidebarView = 'history' | 'pinned' | 'cases' | 'bookmarks' | 'saved-searches' | 'tags' | 'archived' | 'folders' | 'none'
export type IntelligencePanelView = 'leads' | 'entity' | 'evidence' | 'tasks' | 'audit' | 'copilot' | 'reasoning' | 'graph' | 'none'

type UIState = {
  section: PortalSection
  sidebarOpen: boolean
  sidebarView: SidebarView
  intelligenceOpen: boolean
  intelligenceView: IntelligencePanelView
  locale: 'en' | 'kn'
  dashboardOpen: boolean
  commandPaletteOpen: boolean
  darkMode: boolean
  mobileSidebarOpen: boolean
  mobileRightPanelOpen: boolean
  setSection: (section: PortalSection) => void
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
  setSidebarView: (view: SidebarView) => void
  setIntelligenceOpen: (open: boolean) => void
  toggleIntelligence: () => void
  setIntelligenceView: (view: IntelligencePanelView) => void
  setDashboardOpen: (open: boolean) => void
  toggleDashboard: () => void
  setCommandPaletteOpen: (open: boolean) => void
  toggleDarkMode: () => void
  setMobileSidebarOpen: (open: boolean) => void
  setMobileRightPanelOpen: (open: boolean) => void
}

const storedDark = (() => {
  try { return localStorage.getItem('anvaya_dark') === 'true' } catch { return false }
})()

if (storedDark) {
  document.documentElement.classList.add('dark')
}

export const useUIStore = create<UIState>((set, get) => ({
  section: 'chat',
  sidebarOpen: false,
  sidebarView: 'none',
  intelligenceOpen: false,
  intelligenceView: 'none',
  locale: 'en',
  dashboardOpen: true,
  commandPaletteOpen: false,
  darkMode: storedDark,
  mobileSidebarOpen: false,
  mobileRightPanelOpen: false,
  setSection: (section) => set({ section }),
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  toggleSidebar: () => set({ sidebarOpen: !get().sidebarOpen }),
  setSidebarView: (sidebarView) => set({ sidebarView, sidebarOpen: sidebarView !== 'none' }),
  setIntelligenceOpen: (intelligenceOpen) => set({ intelligenceOpen }),
  toggleIntelligence: () => set({ intelligenceOpen: !get().intelligenceOpen }),
  setIntelligenceView: (intelligenceView) =>
    set({ intelligenceView, intelligenceOpen: intelligenceView !== 'none' }),
  setDashboardOpen: (dashboardOpen) => set({ dashboardOpen }),
  toggleDashboard: () => set({ dashboardOpen: !get().dashboardOpen }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setMobileSidebarOpen: (mobileSidebarOpen) => set({ mobileSidebarOpen }),
  setMobileRightPanelOpen: (mobileRightPanelOpen) => set({ mobileRightPanelOpen }),
  toggleDarkMode: () => {
    const next = !get().darkMode
    if (next) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    try { localStorage.setItem('anvaya_dark', String(next)) } catch { /* noop */ }
    set({ darkMode: next })
  },
}))
