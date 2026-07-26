import { type ReactNode } from 'react'

export function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex animate-slide-in-right justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-gradient-to-br from-teal-600 to-teal-800 px-4 py-2.5 text-sm text-white shadow-bubble">
        {text}
      </div>
    </div>
  )
}

export function Assistant({ children }: { children: ReactNode }) {
  return (
    <div className="flex animate-fade-in-up gap-3">
      <div className="mt-1 hidden h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-navy-900 to-teal-800 text-center text-xs font-bold leading-8 text-teal-300 shadow-sm ring-1 ring-teal-500/30 sm:block">
        AN
      </div>
      <div className="min-w-0 flex-1 space-y-3">{children}</div>
    </div>
  )
}

export function Bubble({ children }: { children: ReactNode }) {
  return (
    <div className="inline-block max-w-full rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-bubble">
      {children}
    </div>
  )
}

export function EngineBadge({ engine }: { engine: string }) {
  const isAI = engine === 'ai_assisted' || engine === 'ai-assisted'
  return (
    <span
      className={`animate-scale-in rounded-full px-2 py-0.5 text-[10px] font-semibold ${
        isAI
          ? 'bg-purple-100 text-purple-800 ring-1 ring-purple-200'
          : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
      }`}
    >
      {isAI ? '✦ AI-assisted' : 'Deterministic'}
    </span>
  )
}

export function TypingIndicator() {
  return (
    <Assistant>
      <Bubble>
        <span className="inline-flex items-center gap-1.5 text-slate-500">
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:300ms]" />
          <span className="ml-1">Working…</span>
        </span>
      </Bubble>
    </Assistant>
  )
}
