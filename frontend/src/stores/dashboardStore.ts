import { create } from 'zustand'

export type WidgetId = 'recent-investigations' | 'source-health' | 'shift-briefing' | 'crime-trends' | 'quick-stats' | 'alerts'

export type WidgetConfig = {
  id: WidgetId
  visible: boolean
  order: number
  title: string
}

type DashboardState = {
  widgets: WidgetConfig[]
  widgetData: Record<string, any>
  setWidgetData: (id: string, data: any) => void
  toggleWidget: (id: WidgetId) => void
  reorderWidgets: (ids: WidgetId[]) => void
}

const defaultWidgets: WidgetConfig[] = [
  { id: 'recent-investigations', visible: true, order: 0, title: 'Recent Investigations' },
  { id: 'source-health', visible: true, order: 1, title: 'Source Health' },
  { id: 'shift-briefing', visible: true, order: 2, title: 'Shift Briefing' },
  { id: 'crime-trends', visible: true, order: 3, title: 'Crime Trends' },
  { id: 'quick-stats', visible: true, order: 4, title: 'Quick Stats' },
  { id: 'alerts', visible: true, order: 5, title: 'Alerts' },
]

export const useDashboardStore = create<DashboardState>((set) => ({
  widgets: defaultWidgets,
  widgetData: {},
  setWidgetData: (id, data) => set((s) => ({ widgetData: { ...s.widgetData, [id]: data } })),
  toggleWidget: (id) => set((s) => ({ widgets: s.widgets.map((w) => w.id === id ? { ...w, visible: !w.visible } : w) })),
  reorderWidgets: (ids) => set((s) => ({
    widgets: ids.map((id, i) => ({ ...s.widgets.find((w) => w.id === id)!, order: i })).sort((a, b) => a.order - b.order),
  })),
}))
