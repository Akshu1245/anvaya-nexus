type ChatHelpProps = {
  open: boolean
  onClose: () => void
  onAsk: (text: string) => void
  onStartGuidedDemo: () => void
  onExportPdf: () => void
}

const phrases = [
  'shift briefing',
  'crime trends',
  'complete details',
  'send me PDF',
  'export chat',
  'Find unresolved chain snatching near Jayanagar',
]

export function ChatHelp({ open, onClose, onAsk, onStartGuidedDemo, onExportPdf }: ChatHelpProps) {
  if (!open) return null

  return (
    <aside aria-label="ANVAYA help" className="fixed bottom-20 right-5 z-30 w-[min(22rem,calc(100vw-2.5rem))] rounded-2xl border border-blue-200 bg-white p-5 shadow-2xl">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-navy-950">Try these phrases</h3>
        <button type="button" aria-label="Close help" onClick={onClose} className="text-slate-400 hover:text-slate-700">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">
        {phrases.map((phrase) => (
          <li key={phrase}>
            <button
              type="button"
              className="w-full rounded-lg bg-slate-50 px-3 py-2 text-left hover:bg-blue-50"
              onClick={() => {
                onClose()
                onAsk(phrase)
              }}
            >
              {phrase}
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => {
          onClose()
          onStartGuidedDemo()
        }}
        className="mt-4 w-full rounded-lg bg-blue-700 px-3 py-2 text-sm font-bold text-white hover:bg-blue-800"
      >
        Start guided demo
      </button>
      <button
        type="button"
        onClick={() => {
          onClose()
          onExportPdf()
        }}
        className="mt-2 w-full rounded-lg border border-blue-300 bg-white px-3 py-2 text-sm font-bold text-blue-800 hover:bg-blue-50"
      >
        Export conversation PDF
      </button>
    </aside>
  )
}
