import { useEffect, useCallback, useState } from 'react'

type Shortcut = {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
  label: string
  action: () => void
}

type Command = {
  id: string
  label: string
  icon?: string
  category: string
  action: () => void
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      for (const sc of shortcuts) {
        const ctrl = sc.ctrl !== false || (sc.ctrl === undefined && sc.meta !== true)
        const matchCtrl = sc.meta ? e.metaKey : sc.ctrl ? e.ctrlKey : true
        const matchShift = sc.shift ? e.shiftKey : !e.shiftKey
        const matchAlt = sc.alt ? e.altKey : !e.altKey
        const matchKey = e.key.toLowerCase() === sc.key.toLowerCase()

        if (matchCtrl && matchShift && matchAlt && matchKey) {
          e.preventDefault()
          sc.action()
          return
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [shortcuts])
}

const shortcutList: { key: string; label: string; combo: string }[] = [
  { key: 'k', label: 'Command palette', combo: 'Ctrl+K' },
  { key: 'n', label: 'New conversation', combo: 'Ctrl+N' },
  { key: '/', label: 'Focus search', combo: '/' },
  { key: 'b', label: 'Toggle sidebar', combo: 'Ctrl+B' },
  { key: 'i', label: 'Toggle intelligence panel', combo: 'Ctrl+I' },
  { key: 'Enter', label: 'Send message', combo: 'Enter' },
  { key: 'Escape', label: 'Close panels', combo: 'Esc' },
  { key: 'h', label: 'Open help', combo: 'Ctrl+H' },
  { key: 'p', label: 'Export conversation', combo: 'Ctrl+P' },
]

export function ShortcutGuide() {
  return (
    <div className="space-y-1.5">
      {shortcutList.map((s) => (
        <div key={s.key} className="flex items-center justify-between text-xs">
          <span className="text-slate-600">{s.label}</span>
          <kbd className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">
            {s.combo}
          </kbd>
        </div>
      ))}
    </div>
  )
}

export function useCommandPalette(commands: Command[]) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const filtered = query
    ? commands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.category.toLowerCase().includes(query.toLowerCase()),
      )
    : commands

  const palette = open ? (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" role="dialog" aria-modal="true">
      <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="relative z-10 w-full max-w-lg animate-fade-in-up rounded-2xl border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-slate-400"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.3-4.3"/></svg>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command..."
            className="min-w-0 flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-slate-400"
          />
          <kbd className="rounded border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-400">Esc</kbd>
        </div>
        <div className="max-h-64 overflow-y-auto p-2">
          {filtered.length === 0 && (
            <p className="py-6 text-center text-xs text-slate-400">No commands match "{query}"</p>
          )}
          {filtered.map((cmd) => (
            <button
              key={cmd.id}
              type="button"
              onClick={() => { cmd.action(); setOpen(false); setQuery('') }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-50"
            >
              {cmd.icon && <span className="text-base">{cmd.icon}</span>}
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-800">{cmd.label}</p>
                <p className="text-[11px] text-slate-400">{cmd.category}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  ) : null

  return { palette, open, setOpen, query, setQuery }
}
