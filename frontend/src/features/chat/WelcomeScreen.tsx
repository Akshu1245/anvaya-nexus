import { memo } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useLocale } from '../../i18n/portal'

type Props = { onPromptClick: (text: string) => void }

export const WelcomeScreen = memo(function WelcomeScreen({ onPromptClick }: Props) {
  const user = useAuthStore((s) => s.user)
  const { locale, t } = useLocale()
  const firstName = user?.username?.split('.')?.[0] || user?.username || ''
  const displayName = firstName.charAt(0).toUpperCase() + firstName.slice(1)

  const prompts = locale === 'kn' ? [
    {
      icon: '🔍',
      label: 'ವಾಹನದ ಮೂಲಕ FIR ಹುಡುಕಿ (Search FIR by Vehicle)',
      query: 'ವಾಹನ ಸಂಖ್ಯೆ KA-01-AB-1234 ಇರುವ FIR ಹುಡುಕಿ (Find FIR with vehicle number KA-01-AB-1234)',
      category: 'Search',
    },
    {
      icon: '📋',
      label: 'ಕೇಸ್ ಸಾರಾಂಶ (Case Summary)',
      query: 'SYN-FIR-1034 ಪ್ರಕರಣದ ಸಾರಾಂಶ ನೀಡಿ (Summarize case SYN-FIR-1034)',
      category: 'Case 360',
    },
    {
      icon: '📊',
      label: 'ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು (Crime Trends)',
      query: 'ಕಳೆದ 6 ತಿಂಗಳ ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳನ್ನು ತೋರಿಸಿ (Show recorded crime trends for last 6 months)',
      category: 'Analytics',
    },
    {
      icon: '⚖️',
      label: 'ಬಾಕಿ ಇರುವ ತನಿಖೆಗಳು (Pending Investigations)',
      query: 'SYN-STN-01 ಠಾಣೆಯ ಬಾಕಿ ಪ್ರಕರಣಗಳನ್ನು ತೋರಿಸಿ (Show unresolved cases at SYN-STN-01)',
      category: 'Copilot',
    },
    {
      icon: '🔗',
      label: 'ನೆಟ್‌ವರ್ಕ್ ಸಂಪರ್ಕಗಳು (Network Connections)',
      query: 'ಸಂಬಂಧಿತ ಪ್ರಕರಣಗಳು ಮತ್ತು ಜಾಲವನ್ನು ತೋರಿಸಿ (Show related cases and network for SYN-FIR-1034)',
      category: 'Intelligence',
    },
    {
      icon: '📄',
      label: 'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ (Shift Briefing)',
      query: 'ನನ್ನ ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ತೋರಿಸಿ (Show my shift briefing)',
      category: 'Shift',
    },
  ] : [
    {
      icon: '🔍',
      label: 'Search FIR by Vehicle',
      query: 'Find FIR with vehicle number KA-01-AB-1234',
      category: 'Search',
    },
    {
      icon: '📋',
      label: 'Case Summary',
      query: 'Summarize case SYN-FIR-1034',
      category: 'Case 360',
    },
    {
      icon: '📊',
      label: 'Crime Trends',
      query: 'Show recorded crime trends for last 6 months',
      category: 'Analytics',
    },
    {
      icon: '⚖️',
      label: 'Pending Investigations',
      query: 'Show unresolved chain snatching cases at SYN-STN-01',
      category: 'Copilot',
    },
    {
      icon: '🔗',
      label: 'Network Connections',
      query: 'Show related cases and network connections for SYN-FIR-1034',
      category: 'Intelligence',
    },
    {
      icon: '📄',
      label: 'Shift Briefing',
      query: 'Show my shift briefing',
      category: 'Shift',
    },
  ]

  const capabilityTags = locale === 'kn'
    ? ['FIR ಹುಡುಕಾಟ (FIR Search)', 'ಕೇಸ್ ೩೬೦ (Case 360)', 'ಗ್ರಾಫ್ ವಿಶ್ಲೇಷಣೆ (Graph Analysis)', 'ಎಐ ಕಾಪೈಲಟ್ (AI Copilot)', 'ಡಾಸಿಯರ್ PDF (Dossier PDF)', 'ಧ್ವನಿ ಇನ್‌ಪುಟ್ (Voice Input)']
    : ['FIR Search', 'Case 360', 'Graph Analysis', 'AI Copilot', 'Dossier PDF', 'Voice Input']

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center px-4 py-16 text-center animate-fade-in">

      {/* Avatar / logo */}
      <div className="relative mb-6">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-teal-700 shadow-xl shadow-teal-200 dark:shadow-teal-900/40">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l8 3v6c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V6l8-3z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
        </div>
        <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-400 border-2 border-white dark:border-slate-900 text-[9px] font-bold text-white">AI</span>
      </div>

      {/* Greeting */}
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
        {t('chat.welcomeTitle')}
      </h1>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-sm">
        {t('chat.welcomeSub')}
      </p>

      {/* Capability tags */}
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        {capabilityTags.map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Prompt cards */}
      <div className="mt-8 grid w-full grid-cols-1 gap-2 sm:grid-cols-2 animate-stagger">
        {prompts.map((p) => (
          <button
            key={p.label}
            onClick={() => onPromptClick(p.query)}
            className="group flex items-start gap-3.5 rounded-xl border border-slate-200 bg-white p-4 text-left transition-all hover:border-teal-300 hover:shadow-md hover:shadow-teal-50 dark:border-slate-700 dark:bg-slate-800/60 dark:hover:border-teal-700 dark:hover:shadow-teal-900/20"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-base group-hover:bg-teal-50 dark:bg-slate-700 dark:group-hover:bg-teal-900/30 transition-colors">
              {p.icon}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{p.label}</p>
              <p className="mt-0.5 truncate text-[11px] text-slate-400 dark:text-slate-500">{p.query}</p>
            </div>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="ml-auto mt-0.5 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100 dark:text-slate-600"
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        ))}
      </div>

      <p className="mt-8 text-[11px] text-slate-400 dark:text-slate-600">
        {locale === 'kn'
          ? 'ಎಲ್ಲಾ ಡೇಟಾ ಸಿಂಥೆಟಿಕ್ ಆಗಿದೆ · ಮಾನವ ವಿಮರ್ಶೆ ಕಡ್ಡಾಯ (All data is synthetic · Human review required for all AI insights)'
          : 'All data is synthetic · Human review required for all AI insights'}
      </p>
    </div>
  )
})
