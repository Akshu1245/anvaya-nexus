export function VoiceTranscript({ text, language, isFinal }: { text: string; language?: string; isFinal?: boolean }) {
  if (!text) return null
  return (
    <div className={`animate-fade-in rounded-lg border px-3 py-2 text-sm ${
      isFinal
        ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
        : 'border-slate-200 bg-white text-slate-600 italic'
    }`}>
      <div className="flex items-center gap-2">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="shrink-0">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="23"/>
          <line x1="8" y1="23" x2="16" y2="23"/>
        </svg>
        <span className="flex-1">{text}</span>
        {language && (
          <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
            {language}
          </span>
        )}
      </div>
    </div>
  )
}

export function MixedLanguageIndicator({ languages }: { languages: string[] }) {
  if (!languages?.length) return null
  return (
    <div className="flex flex-wrap gap-1">
      {languages.map((lang) => (
        <span key={lang} className="rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-medium text-purple-700 ring-1 ring-purple-200">
          {lang === 'kn-IN' ? 'ಕನ್ನಡ' : lang === 'hi-IN' ? 'हिन्दी' : lang === 'en-IN' ? 'English' : lang}
        </span>
      ))}
    </div>
  )
}
