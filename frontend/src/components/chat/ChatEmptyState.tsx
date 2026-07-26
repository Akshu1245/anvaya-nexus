import { useLocale } from '../../i18n/portal'
import { OFFENCE_CATALOGUE } from '../OffenceVisual'

type ChatEmptyStateProps = {
  examples: string[]
  ask: (text: string) => void
  aiAssistEnabled?: boolean
}

export function ChatEmptyState({ examples, ask, aiAssistEnabled }: ChatEmptyStateProps) {
  const { t } = useLocale()

  return (
    <div className="animate-fade-in-up rounded-2xl border border-slate-200 bg-white p-6 shadow-bubble">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-navy-900 text-white shadow-sm">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M5 5h14v10H9l-4 4z"/><path d="M8 9h8M8 12h5"/>
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold">Ask everything here</h3>
          <p className="text-xs text-slate-500">{t('aboutLead')}</p>
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600">
        There are no separate menus for search, briefing, trends, Case 360 or briefs. Type or speak what you need — ANVAYA answers only from authorised synthetic records, with confirmation and source citations.
      </p>
      {aiAssistEnabled && (
        <p className="mt-2 rounded-lg bg-purple-50 p-2 text-xs text-purple-800 ring-1 ring-purple-100">
          ✦ AI Assist is active — questions may be interpreted by AI, while answers remain bounded to synthetic prototype records.
        </p>
      )}
      <div className="mt-4 grid gap-2 sm:grid-cols-4">
        {OFFENCE_CATALOGUE.slice(0, 4).map((item, index) => (
          <button
            key={item.code}
            type="button"
            style={{ animationDelay: `${index * 70}ms` }}
            className="animate-fade-in-up overflow-hidden rounded-xl border border-slate-200 bg-white text-left shadow-bubble transition-all hover:-translate-y-0.5 hover:border-teal-400 hover:shadow-panel"
            onClick={() => ask(`Find unresolved ${item.label.toLowerCase()} cases`)}
          >
            <img src={item.src} alt="" className="aspect-[4/3] w-full object-contain" loading="lazy" />
            <span className="block border-t border-slate-100 bg-white px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-navy-950">
              {item.label}
            </span>
          </button>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {examples.map((example, index) => (
          <button
            key={example}
            style={{ animationDelay: `${index * 80}ms` }}
            className="animate-fade-in-up rounded-full border border-slate-300 px-3 py-1.5 text-xs transition-all hover:-translate-y-0.5 hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 hover:shadow-sm"
            onClick={() => ask(example)}
          >
            {example}
          </button>
        ))}
      </div>
      <div className="mt-5 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-4">
        {[
          { step: '1', title: 'Ask in chat', text: 'Type or speak — search, briefing, trends, everything starts here.' },
          { step: '2', title: 'Confirm', text: 'Review how ANVAYA read it — edit filters before anything runs.' },
          { step: '3', title: 'Inspect in thread', text: 'Case 360, related cases and graphs open as chat replies.' },
          { step: '4', title: 'Brief', text: 'Ask for a grounded brief — download cited PDF from the reply.' },
        ].map((item, index) => (
          <div
            key={item.step}
            style={{ animationDelay: `${index * 90}ms` }}
            className="animate-fade-in-up rounded-xl bg-slate-50 p-3 ring-1 ring-slate-100"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-teal-600 to-teal-800 text-[11px] font-bold text-white">
              {item.step}
            </span>
            <p className="mt-2 text-xs font-bold text-navy-950">{item.title}</p>
            <p className="mt-0.5 text-[11px] leading-4 text-slate-500">{item.text}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xl border border-teal-100 bg-teal-50/50 px-3 py-2 text-[11px] text-teal-900">
        <span className="font-bold uppercase tracking-wide">Safeguards active</span>
        <span>Server-side policy</span>
        <span>Jurisdiction masking</span>
        <span>Full audit trail</span>
        <span>Human confirmation</span>
        <span>Source citations</span>
      </div>
      <p className="mt-4 text-center text-xs text-slate-500">Need help? Open the persistent Help button (bottom-right) for guided steps and features.</p>
    </div>
  )
}
