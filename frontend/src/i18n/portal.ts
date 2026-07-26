import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  useEffect,
  type ReactNode,
} from 'react'

export type Locale = 'en' | 'kn'

export const LOCALE_STORAGE_KEY = 'anvaya_locale'

const en: Record<string, string> = {
  // Navigation
  'nav.home': 'AI Chat',
  'nav.dashboard': 'Dashboard',
  'nav.analytics': 'Crime Analytics',
  'nav.reports': 'Investigation Reports',
  'nav.evidence': 'Evidence Repository',
  'nav.supervisor': 'Supervisor Panel',
  'nav.settings': 'Settings',
  'nav.search': 'Search',
  'nav.briefing': 'Shift Briefing',
  'nav.trends': 'Crime Trends',
  'nav.chat': 'Investigation Chat',
  'nav.about': 'About ANVAYA',
  'nav.helplines': 'Helplines 112',
  'nav.privacy': 'Privacy',
  'nav.screenReader': 'Screen Reader Access',
  'nav.bookmarks': 'Bookmarks',
  'nav.logout': 'Logout',
  'nav.newChat': 'New Chat',
  'nav.searchConvs': 'Search conversations...',

  // App Shell & TopBar
  'ksp.title': 'Karnataka State Police',
  'ksp.portal': 'KSP Portal',
  'topbar.searchPlaceholder': 'Search...',
  'topbar.intel': 'Intel',

  // Landing Page
  'landing.heroTitle': 'Karnataka State Police Intelligence Platform',
  'landing.heroSubtitle': 'Conversational AI for fast FIR analysis, evidence tracking, and court-ready dossiers.',
  'landing.loginBtn': 'Officer Login Portal',
  'landing.registerBtn': 'Register Officer ID',
  'landing.featuresTitle': 'Investigation Intelligence Features',
  'landing.aboutTitle': 'About Karnataka Police ANVAYA',
  'landing.aboutDesc': 'ANVAYA is designed for Karnataka State Police officers to query CCTNS FIR databases, visualize crime patterns, track physical evidence, and generate cited dossiers.',

  // Dashboard
  'dash.title': 'Dashboard',
  'dash.subtitle': 'Overview of state-wide FIR metrics, active cases, and priority alerts.',
  'dash.totalFirs': 'Total FIR Records',
  'dash.pendingCases': 'Pending Investigations',
  'dash.resolvedCases': 'Resolved Cases',
  'dash.priorityAlerts': 'Priority Actions',
  'dash.recentTrends': 'Recent Crime Trends',
  'dash.quickActions': 'Quick Actions',

  // Evidence
  'evidence.title': 'Evidence Repository',
  'evidence.subtitle': 'Track physical exhibits, custody tags, forensic status, and chain of custody.',
  'evidence.searchPlaceholder': 'Search evidence by ID, case number, or station...',
  'evidence.filterStation': 'Filter by Station',
  'evidence.filterStatus': 'Filter by Status',

  // Reports
  'reports.title': 'Investigation Reports',
  'reports.subtitle': 'Create, manage, and download official investigation briefs and dossiers anytime.',
  'reports.createBtn': '+ Create Report',
  'reports.downloadPdf': 'Download PDF',
  'reports.noReports': 'No Investigation Reports Yet',
  'reports.modalTitle': 'Create Investigation Report',
  'reports.fieldTitle': 'Report Title *',
  'reports.fieldNotes': 'Investigation Summary & Findings',
  'reports.submitBtn': 'Create & Save Report',

  // Chat & Composer
  'chat.placeholder': 'Ask in English, ಕನ್ನಡ, or हिन्दी...',
  'chat.recording': 'Recording... Speak now (Real-time transcript updates below)',
  'chat.stopRecording': 'DONE / STOP',
  'chat.welcomeTitle': 'Karnataka State Police AI Copilot',
  'chat.welcomeSub': 'Ask any question about FIRs, crime trends, suspect links, or shift briefings.',

  // Common UI
  skipWorkspace: 'Skip to workspace',
  emergency: 'Emergency 112',
  online: '● Online',
  offline: 'Offline — data access paused',
  prototypeBanner: 'KARNATAKA STATE POLICE · ANVAYA NEXUS PLATFORM',
  close: 'Close',
  cancel: 'Cancel',
  retry: 'Retry',
  confirm: 'Confirm',
  download: 'Download',
  loading: 'Loading…',
  back: 'Back',
  next: 'Next',
  save: 'Save',
  clear: 'Clear filters',
  english: 'English',
  kannada: 'ಕನ್ನಡ',
}

// Every Kannada item formatted as: "Kannada Text (English Text)"
const kn: Record<string, string> = {
  // Navigation
  'nav.home': 'ಎಐ ತನಿಖಾ ಚಾಟ್ (AI Chat)',
  'nav.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ (Dashboard)',
  'nav.analytics': 'ಅಪರಾಧ ವಿಶ್ಲೇಷಣೆ (Crime Analytics)',
  'nav.reports': 'ತನಿಖಾ ವರದಿಗಳು (Investigation Reports)',
  'nav.evidence': 'ಸಾಕ್ಷ್ಯ ಭಂಡಾರ (Evidence Repository)',
  'nav.supervisor': 'ಮೇಲ್ವಿಚಾರಕರ ಫಲಕ (Supervisor Panel)',
  'nav.settings': 'ಸಂಯೋಜನೆಗಳು (Settings)',
  'nav.search': 'ಹುಡುಕಾಟ (Search)',
  'nav.briefing': 'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ (Shift Briefing)',
  'nav.trends': 'ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು (Crime Trends)',
  'nav.chat': 'ತನಿಖಾ ಚಾಟ್ (Investigation Chat)',
  'nav.about': 'ಅನ್ವಯ ಬಗ್ಗೆ (About ANVAYA)',
  'nav.helplines': 'ಸಹಾಯವಾಣಿ ೧೧೨ (Helplines 112)',
  'nav.privacy': 'ಗೌಪ್ಯತೆ (Privacy)',
  'nav.screenReader': 'ಸ್ಕ್ರೀನ್ ರೀಡರ್ ಪ್ರವೇಶ (Screen Reader Access)',
  'nav.bookmarks': 'ಬುಕ್‌ಮಾರ್ಕ್‌ಗಳು (Bookmarks)',
  'nav.logout': 'ನಿರ್ಗಮಿಸಿ (Logout)',
  'nav.newChat': 'ಹೊಸ ಚಾಟ್ (New Chat)',
  'nav.searchConvs': 'ಸಂಭಾಷಣೆಗಳನ್ನು ಹುಡುಕಿ... (Search conversations...)',

  // App Shell & TopBar
  'ksp.title': 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ (Karnataka State Police)',
  'ksp.portal': 'ಕೆಎಸ್‌ಪಿ ಪೋರ್ಟಲ್ (KSP Portal)',
  'topbar.searchPlaceholder': 'ಹುಡುಕಿ... (Search...)',
  'topbar.intel': 'ಬುದ್ಧಿಮತ್ತೆ (Intel)',

  // Landing Page
  'landing.heroTitle': 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ ತನಿಖಾ ಬುದ್ಧಿಮತ್ತೆ ವೇದಿಕೆ (KSP Intelligence Platform)',
  'landing.heroSubtitle': 'FIR ವಿಶ್ಲೇಷಣೆ, ಸಾಕ್ಷ್ಯ ಟ್ರ್ಯಾಕಿಂಗ್ ಮತ್ತು ನ್ಯಾಯಾಲಯದ ವರದಿಗಳಿಗಾಗಿ ಸಂಭಾಷಣಾ ಎಐ (Conversational AI for FIR Analysis)',
  'landing.loginBtn': 'ಅಧಿಕಾರಿಗಳ ಲಾಗಿನ್ (Officer Login)',
  'landing.registerBtn': 'ಅಧಿಕಾರಿ ಐಡಿ ನೋಂದಣಿ (Register Officer ID)',
  'landing.featuresTitle': 'ತನಿಖಾ ಬುದ್ಧಿಮತ್ತೆಯ ವೈಶಿಷ್ಟ್ಯಗಳು (Intelligence Features)',
  'landing.aboutTitle': 'ಕರ್ನಾಟಕ ಪೊಲೀಸ್ ಅನ್ವಯ ಬಗ್ಗೆ (About KSP ANVAYA)',
  'landing.aboutDesc': 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ ಅಧಿಕಾರಿಗಳಿಗಾಗಿ CCTNS FIR ಡೇಟಾಬೇಸ್‌ಗಳನ್ನು ಪ್ರಶ್ನಿಸಲು, ಅಪರಾಧ ಮಾದರಿಗಳನ್ನು ವೀಕ್ಷಿಸಲು ಮತ್ತು ವರದಿಗಳನ್ನು ನಿರ್ಮಿಸಲು ಅನ್ವಯ ವಿನ್ಯಾಸಗೊಳಿಸಲಾಗಿದೆ (Designed for KSP FIR Querying)',

  // Dashboard
  'dash.title': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ (Dashboard)',
  'dash.subtitle': 'ರಾಜ್ಯಾದ್ಯಂತ FIR ಅಂಕಿಅಂಶಗಳು, ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳು ಮತ್ತು ಆದ್ಯತೆಯ ಎಚ್ಚರಿಕೆಗಳ ಅವಲೋಕನ (State-wide FIR Metrics Overview)',
  'dash.totalFirs': 'ಒಟ್ಟು FIR ದಾಖಲೆಗಳು (Total FIR Records)',
  'dash.pendingCases': 'ಬಾಕಿ ಇರುವ ತನಿಖೆಗಳು (Pending Investigations)',
  'dash.resolvedCases': 'ಪರಿಹರಿಸಲಾದ ಪ್ರಕರಣಗಳು (Resolved Cases)',
  'dash.priorityAlerts': 'ಆದ್ಯತೆಯ ಕ್ರಮಗಳು (Priority Actions)',
  'dash.recentTrends': 'ಇತ್ತೀಚಿನ ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು (Recent Crime Trends)',
  'dash.quickActions': 'ತ್ವರಿತ ಕ್ರಮಗಳು (Quick Actions)',

  // Evidence
  'evidence.title': 'ಸಾಕ್ಷ್ಯ ಭಂಡಾರ (Evidence Repository)',
  'evidence.subtitle': 'ಭೌತಿಕ ಸಾಕ್ಷ್ಯಗಳು, ಕಸ್ಟಡಿ ಟ್ಯಾಗ್‌ಗಳು, ವಿಧಿವಿಜ್ಞಾನ ಸ್ಥಿತಿ ಮತ್ತು ಸರಣಿಯನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ (Track Physical & Digital Evidence)',
  'evidence.searchPlaceholder': 'ಸಾಕ್ಷ್ಯ ಐಡಿ, ಕೇಸ್ ಸಂಖ್ಯೆ ಅಥವಾ ಠಾಣೆಯ ಮೂಲಕ ಹುಡುಕಿ... (Search Evidence ID/Case/Station)',
  'evidence.filterStation': 'ಠಾಣೆಯ ಪ್ರಕಾರ ಫಿಲ್ಟರ್ ಮಾಡಿ (Filter by Station)',
  'evidence.filterStatus': 'ಸ್ಥಿತಿಯ ಪ್ರಕಾರ ಫಿಲ್ಟರ್ ಮಾಡಿ (Filter by Status)',

  // Reports
  'reports.title': 'ತನಿಖಾ ವರದಿಗಳು (Investigation Reports)',
  'reports.subtitle': 'ಅಧಿಕೃತ ತನಿಖಾ ವರದಿಗಳನ್ನು ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ರಚಿಸಿ, ನಿರ್ವಹಿಸಿ ಮತ್ತು PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (Create & Download Dossiers Anytime)',
  'reports.createBtn': '+ ಹೊಸ ವರದಿ ರಚಿಸಿ (+ Create Report)',
  'reports.downloadPdf': 'PDF ಡೌನ್‌ಲೋಡ್ (Download PDF)',
  'reports.noReports': 'ಇನ್ನೂ ಯಾವುದೇ ವರದಿಗಳಿಲ್ಲ (No Reports Yet)',
  'reports.modalTitle': 'ಹೊಸ ತನಿಖಾ ವರದಿ ರಚಿಸಿ (Create Investigation Report)',
  'reports.fieldTitle': 'ವರದಿಯ ಶೀರ್ಷಿಕೆ * (Report Title *)',
  'reports.fieldNotes': 'ತನಿಖಾ ವಿವರಗಳು ಮತ್ತು ನಿರ್ಣಯಗಳು (Summary & Findings)',
  'reports.submitBtn': 'ವರದಿ ಉಳಿಸಿ (Save Report)',

  // Chat & Composer
  'chat.placeholder': 'ಇಂಗ್ಲಿಷ್, ಕನ್ನಡ ಅಥವಾ ಹಿಂದಿಯಲ್ಲಿ ಕೇಳಿ... (Ask in English, Kannada, or Hindi...)',
  'chat.recording': 'ರೆಕಾರ್ಡ್ ಆಗುತ್ತಿದೆ... ಮಾತನಾಡಿ (Recording... Speak now)',
  'chat.stopRecording': 'ಮುಕ್ತಾಯ / ನಿಲ್ಲಿಸಿ (DONE / STOP)',
  'chat.welcomeTitle': 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ ಎಐ ಸಹಾಯಕ (KSP AI Copilot)',
  'chat.welcomeSub': 'FIRಗಳು, ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು ಅಥವಾ ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ಬಗ್ಗೆ ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕೇಳಿ (Ask any FIR question)',

  // Common UI
  skipWorkspace: 'ಕಾರ್ಯಕ್ಷೇತ್ರಕ್ಕೆ ಹೋಗಿ (Skip to Workspace)',
  emergency: 'ತುರ್ತು ೧೧೨ (Emergency 112)',
  online: '● ಆನ್‌ಲೈನ್ (Online)',
  offline: 'ಆಫ್‌ಲೈನ್ (Offline)',
  prototypeBanner: 'ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ · ಅನ್ವಯ ನೆಕ್ಸಸ್ ವೇದಿಕೆ (KARNATAKA STATE POLICE · ANVAYA NEXUS)',
  close: 'ಮುಚ್ಚಿ (Close)',
  cancel: 'ರದ್ದುಮಾಡಿ (Cancel)',
  retry: 'ಮರುಪ್ರಯತ್ನ (Retry)',
  confirm: 'ದೃಢೀಕರಿಸಿ (Confirm)',
  download: 'ಡೌನ್‌ಲೋಡ್ (Download)',
  loading: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ… (Loading…)',
  back: 'ಹಿಂದೆ (Back)',
  next: 'ಮುಂದೆ (Next)',
  save: 'ಉಳಿಸಿ (Save)',
  clear: 'ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಅಳಿಸಿ (Clear Filters)',
  english: 'English',
  kannada: 'ಕನ್ನಡ (English)',
}

const dictionaries: Record<Locale, Record<string, string>> = { en, kn }

function readStoredLocale(): Locale {
  try {
    const raw = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (raw === 'kn' || raw === 'en') return raw
  } catch {
    /* ignore storage errors */
  }
  return 'en'
}

function persistLocale(locale: Locale) {
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    /* ignore storage errors */
  }
}

export type LocaleContextValue = {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string) => string
}

const LocaleContext = createContext<LocaleContextValue | null>(null)

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() =>
    typeof window === 'undefined' ? 'en' : readStoredLocale(),
  )

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale
    }
  }, [locale])

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    persistLocale(next)
  }, [])

  const t = useCallback(
    (key: string) => {
      const match = dictionaries[locale]?.[key]
      if (match) return match
      const enMatch = dictionaries.en?.[key] || key
      return locale === 'kn' ? `${enMatch} (${enMatch})` : enMatch
    },
    [locale],
  )

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t])

  return createElement(LocaleContext.Provider, { value }, children)
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext)
  if (!ctx) {
    return { locale: 'en', setLocale: () => {}, t: (key: string) => key }
  }
  return ctx
}

export function getPortalDictionary(locale: Locale): Record<string, string> {
  return dictionaries[locale]
}
