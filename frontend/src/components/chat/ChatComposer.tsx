import { useRef, useEffect } from 'react'

type ChatComposerProps = {
  input: string
  onInputChange: (value: string) => void
  onSend: () => void
  onVoiceToggle: () => void
  isRecording: boolean
  isVoiceAvailable: boolean
  isBusy: boolean
  parentMessageId: string
  onNewTopic: () => void
  placeholder?: string
  locale?: string
}

export function ChatComposer({
  input,
  onInputChange,
  onSend,
  onVoiceToggle,
  isRecording,
  isVoiceAvailable,
  isBusy,
  parentMessageId,
  onNewTopic,
  placeholder = 'Ask in English or Kannada…',
}: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }, [input])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <form
      className="sticky bottom-0 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur"
      onSubmit={(e) => {
        e.preventDefault()
        onSend()
      }}
    >
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          aria-label="Ask ANVAYA"
          rows={1}
          className="max-h-40 min-h-11 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:border-teal-500 focus:shadow-glow"
          placeholder={placeholder}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <input
          type="file"
          id="chat-file-upload"
          className="hidden"
          accept=".pdf,.txt,.csv,.json,.md,.log"
          onChange={async (e) => {
            const file = e.target.files?.[0]
            if (!file) return
            try {
              const text = await file.text()
              const cleanText = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '').slice(0, 3000)
              const prefix = input ? `${input}\n` : ''
              onInputChange(`${prefix}[File: ${file.name}]\n${cleanText}`)
            } catch {
              const prefix = input ? `${input}\n` : ''
              onInputChange(`${prefix}[Attached File: ${file.name} (${Math.round(file.size / 1024)} KB)]`)
            }
            e.target.value = ''
          }}
        />
        <label
          htmlFor="chat-file-upload"
          className="flex h-11 shrink-0 cursor-pointer items-center justify-center rounded-xl border border-slate-300 px-3 text-slate-600 hover:border-teal-500 hover:bg-teal-50"
          title="Attach document or case file (.pdf, .txt, .json, .csv)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
          </svg>
        </label>
        <button
          type="button"
          aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
          className={`h-11 shrink-0 rounded-xl border px-3 text-sm disabled:opacity-50 ${
            isRecording
              ? 'animate-pulse-ring border-red-400 bg-red-50 text-red-600'
              : 'border-slate-300 hover:border-teal-500 hover:bg-teal-50'
          }`}
          disabled={!isVoiceAvailable || isBusy}
          onClick={onVoiceToggle}
        >
          {isRecording ? 'Stop' : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          )}
        </button>
        <button
          type="submit"
          className="flex h-11 shrink-0 items-center gap-1.5 rounded-xl bg-gradient-to-br from-teal-600 to-teal-800 px-4 text-sm font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 hover:shadow-glow disabled:opacity-60 disabled:shadow-none"
          disabled={isBusy || !input.trim()}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          Send
        </button>
      </div>
      {!isVoiceAvailable && (
        <p className="mt-1 text-[11px] text-slate-400">Voice recognition is unavailable in this browser; typing works everywhere.</p>
      )}
      {isRecording && (
        <p className="mt-1 text-[11px] text-red-500">Recording… press Stop to transcribe.</p>
      )}
      {parentMessageId && (
        <button
          type="button"
          className="mt-1 text-[11px] text-teal-700 underline hover:text-teal-600"
          onClick={onNewTopic}
        >
          Start a new topic (clear follow-up context)
        </button>
      )}
      <p className="mt-2 rounded-lg bg-blue-50 px-2 py-1.5 text-[11px] leading-4 text-blue-900">
        Prototype only · not monitored · synthetic data only · cannot file an FIR or contact emergency services. Call 112 for emergencies.
      </p>
    </form>
  )
}
