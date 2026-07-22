import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type Locale = 'en' | 'kn'

export const LOCALE_STORAGE_KEY = 'anvaya_locale'

export type PortalDictKey =
  | 'nav.search'
  | 'nav.briefing'
  | 'nav.trends'
  | 'nav.chat'
  | 'nav.about'
  | 'nav.helplines'
  | 'nav.privacy'
  | 'nav.screenReader'
  | 'skipWorkspace'
  | 'emergency'
  | 'online'
  | 'offline'
  | 'prototypeBanner'
  | 'aboutTitle'
  | 'aboutLead'
  | 'helplinesTitle'
  | 'helplinesLead'
  | 'privacyTitle'
  | 'privacyBody'
  | 'searchTitle'
  | 'searchLead'
  | 'filtersTitle'
  | 'resultsTitle'
  | 'resultsEmpty'
  | 'openCase360'
  | 'loadBriefing'
  | 'loadTrends'
  | 'chatAssist'
  | 'send'
  | 'languageNoticeKn'
  | 'purposeLabel'
  | 'sourcesLabel'
  | 'previewQuery'
  | 'searchRecords'
  | 'close'
  | 'cancel'
  | 'retry'
  | 'confirm'
  | 'download'
  | 'loading'
  | 'back'
  | 'next'
  | 'save'
  | 'clear'
  | 'related'
  | 'graph'
  | 'priorities'
  | 'assurance'
  | 'networkClusters'
  | 'prepareBrief'
  | 'downloadDossier'
  | 'english'
  | 'kannada'

type Dictionary = Record<PortalDictKey, string>

const en: Dictionary = {
  'nav.search': 'Search',
  'nav.briefing': 'Shift Briefing',
  'nav.trends': 'Crime Trends',
  'nav.chat': 'Investigation Chat',
  'nav.about': 'About ANVAYA',
  'nav.helplines': 'Helplines',
  'nav.privacy': 'Privacy',
  'nav.screenReader': 'Screen Reader Access',
  skipWorkspace: 'Skip to workspace',
  emergency: 'Emergency',
  online: '● Online',
  offline: 'Offline — data access paused',
  prototypeBanner: 'SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE',
  aboutTitle: 'What we built, and why it matters',
  aboutLead:
    'ANVAYA is a conversational investigation-intelligence prototype for the Karnataka State Police Datathon. Ask in plain language and receive answers only from authorised synthetic FIR records, with a citation for every factual claim.',
  helplinesTitle: 'Helplines',
  helplinesLead:
    'These national helpline numbers are real and available 24×7. Everything else in this prototype is synthetic.',
  privacyTitle: 'Privacy Policy',
  privacyBody:
    'Do not enter personal or operational information. This interface is for synthetic demonstration data only. ANVAYA has no live KSP or CCTNS connection. Static app resources may be cached for resilience; FIR data and API responses are never stored offline.',
  searchTitle: 'Investigation Search',
  searchLead:
    'Set FIR filters or preview a natural-language question, then confirm Search. Nothing is retrieved until you click Search records.',
  filtersTitle: 'FIR filters',
  resultsTitle: 'Search results',
  resultsEmpty:
    'No records yet. Set an offence, date range, station, or case number in the filters, then click Search records.',
  openCase360: 'Open Case 360',
  loadBriefing: 'Load shift briefing',
  loadTrends: 'Load crime trends',
  chatAssist: 'Chat assist',
  send: 'Send',
  languageNoticeKn:
    'UI is Kannada; case text is English (synthetic records). Translation is unavailable right now.',
  purposeLabel: 'Purpose',
  sourcesLabel: 'Sources',
  previewQuery: 'Preview query',
  searchRecords: 'Search records',
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
  related: 'Related cases',
  graph: 'Relationship graph',
  priorities: 'Verification priorities',
  assurance: 'Record assurance',
  networkClusters: 'Network clusters',
  prepareBrief: 'Prepare brief',
  downloadDossier: 'Download dossier PDF',
  english: 'English',
  kannada: 'ಕನ್ನಡ',
}

const kn: Dictionary = {
  'nav.search': 'ಹುಡುಕಾಟ',
  'nav.briefing': 'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್',
  'nav.trends': 'ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು',
  'nav.chat': 'ತನಿಖಾ ಚಾಟ್',
  'nav.about': 'ಅನ್ವಯ ಬಗ್ಗೆ',
  'nav.helplines': 'ಸಹಾಯವಾಣಿ',
  'nav.privacy': 'ಗೌಪ್ಯತೆ',
  'nav.screenReader': 'ಸ್ಕ್ರೀನ್ ರೀಡರ್ ಪ್ರವೇಶ',
  skipWorkspace: 'ಕಾರ್ಯಕ್ಷೇತ್ರಕ್ಕೆ ಹೋಗಿ',
  emergency: 'ತುರ್ತು',
  online: '● ಆನ್‌ಲೈನ್',
  offline: 'ಆಫ್‌ಲೈನ್ — ಡೇಟಾ ಪ್ರವೇಶ ನಿಲ್ಲಿಸಲಾಗಿದೆ',
  prototypeBanner: 'ಸಿಂಥೆಟಿಕ್ ಡೇಟಾಥಾನ್ ಮಾದರಿ — ಕಾರ್ಯಾಚರಣೆಗೆ ಬಳಸಬೇಡಿ',
  aboutTitle: 'ನಾವು ಏನು ನಿರ್ಮಿಸಿದ್ದೇವೆ, ಏಕೆ ಮುಖ್ಯ',
  aboutLead:
    'ಅನ್ವಯ ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ ಡೇಟಾಥಾನ್‌ಗಾಗಿ ನಿರ್ಮಿಸಿದ ಸಂಭಾಷಣಾ ತನಿಖಾ-ಬುದ್ಧಿಮತ್ತೆ ಮಾದರಿ. ಸರಳ ಭಾಷೆಯಲ್ಲಿ ಕೇಳಿ; ಪ್ರತಿ ವಾಸ್ತವಿಕ ಹೇಳಿಕೆಗೆ ಉಲ್ಲೇಖದೊಂದಿಗೆ ಅಧಿಕೃತ ಸಿಂಥೆಟಿಕ್ FIR ದಾಖಲೆಗಳಿಂದ ಮಾತ್ರ ಉತ್ತರಗಳು ಬರುತ್ತವೆ.',
  helplinesTitle: 'ಸಹಾಯವಾಣಿ',
  helplinesLead:
    'ಈ ರಾಷ್ಟ್ರೀಯ ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆಗಳು ನಿಜವಾಗಿಯೂ ೨೪×೭ ಲಭ್ಯ. ಈ ಮಾದರಿಯಲ್ಲಿನ ಇತರೆಲ್ಲವೂ ಸಿಂಥೆಟಿಕ್.',
  privacyTitle: 'ಗೌಪ್ಯತಾ ನೀತಿ',
  privacyBody:
    'ವೈಯಕ್ತಿಕ ಅಥವಾ ಕಾರ್ಯಾಚರಣಾ ಮಾಹಿತಿ ನಮೂದಿಸಬೇಡಿ. ಈ ಮುಖಪುಟ ಸಿಂಥೆಟಿಕ್ ಪ್ರದರ್ಶನ ಡೇಟಾಗೆ ಮಾತ್ರ. ಅನ್ವಯಕ್ಕೆ ನೇರ KSP/CCTNS ಸಂಪರ್ಕವಿಲ್ಲ. ಸ್ಥಿರ ಆ್ಯಪ್ ಸಂಪನ್ಮೂಲಗಳನ್ನು ಕ್ಯಾಶ್ ಮಾಡಬಹುದು; FIR ಡೇಟಾ ಮತ್ತು API ಪ್ರತಿಕ್ರಿಯೆಗಳನ್ನು ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿ ಸಂಗ್ರಹಿಸಲಾಗುವುದಿಲ್ಲ.',
  searchTitle: 'ತನಿಖಾ ಹುಡುಕಾಟ',
  searchLead:
    'FIR ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಹೊಂದಿಸಿ ಅಥವಾ ಸರಳ-ಭಾಷಾ ಪ್ರಶ್ನೆಯನ್ನು ಪೂರ್ವವೀಕ್ಷಿಸಿ, ನಂತರ ಹುಡುಕಾಟವನ್ನು ದೃಢೀಕರಿಸಿ. ನೀವು «ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ» ಕ್ಲಿಕ್ ಮಾಡುವವರೆಗೆ ಏನನ್ನೂ ಪಡೆಯಲಾಗುವುದಿಲ್ಲ.',
  filtersTitle: 'FIR ಫಿಲ್ಟರ್‌ಗಳು',
  resultsTitle: 'ಹುಡುಕಾಟ ಫಲಿತಾಂಶಗಳು',
  resultsEmpty:
    'ಇನ್ನೂ ದಾಖಲೆಗಳಿಲ್ಲ. ಅಪರಾಧ, ದಿನಾಂಕ ಶ್ರೇಣಿ, ಠಾಣೆ ಅಥವಾ ಪ್ರಕರಣ ಸಂಖ್ಯೆಯನ್ನು ಫಿಲ್ಟರ್‌ಗಳಲ್ಲಿ ಹೊಂದಿಸಿ, ನಂತರ «ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ» ಕ್ಲಿಕ್ ಮಾಡಿ.',
  openCase360: 'ಕೇಸ್ ೩೬೦ ತೆರೆಯಿರಿ',
  loadBriefing: 'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ಲೋಡ್ ಮಾಡಿ',
  loadTrends: 'ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಿ',
  chatAssist: 'ಚಾಟ್ ಸಹಾಯ',
  send: 'ಕಳುಹಿಸಿ',
  languageNoticeKn:
    'ಮುಖಪುಟ ಕನ್ನಡದಲ್ಲಿದೆ; ಪ್ರಕರಣ ಪಠ್ಯ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿದೆ (ಸಿಂಥೆಟಿಕ್ ದಾಖಲೆಗಳು). ಅನುವಾದ ಈಗ ಲಭ್ಯವಿಲ್ಲ.',
  purposeLabel: 'ಉದ್ದೇಶ',
  sourcesLabel: 'ಮೂಲಗಳು',
  previewQuery: 'ಪ್ರಶ್ನೆ ಪೂರ್ವವೀಕ್ಷಣೆ',
  searchRecords: 'ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ',
  close: 'ಮುಚ್ಚಿ',
  cancel: 'ರದ್ದುಮಾಡಿ',
  retry: 'ಮರುಪ್ರಯತ್ನ',
  confirm: 'ದೃಢೀಕರಿಸಿ',
  download: 'ಡೌನ್‌ಲೋಡ್',
  loading: 'ಲೋಡ್ ಆಗುತ್ತಿದೆ…',
  back: 'ಹಿಂದೆ',
  next: 'ಮುಂದೆ',
  save: 'ಉಳಿಸಿ',
  clear: 'ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಅಳಿಸಿ',
  related: 'ಸಂಬಂಧಿತ ಪ್ರಕರಣಗಳು',
  graph: 'ಸಂಬಂಧ ಗ್ರಾಫ್',
  priorities: 'ಪರಿಶೀಲನಾ ಆದ್ಯತೆಗಳು',
  assurance: 'ದಾಖಲೆ ಭರವಸೆ',
  networkClusters: 'ಜಾಲ ಸಮೂಹಗಳು',
  prepareBrief: 'ಬ್ರೀಫ್ ತಯಾರಿಸಿ',
  downloadDossier: 'ಡಾಸಿಯರ್ PDF ಡೌನ್‌ಲೋಡ್',
  english: 'English',
  kannada: 'ಕನ್ನಡ',
}

const dictionaries: Record<Locale, Dictionary> = { en, kn }

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
  t: (key: PortalDictKey) => string
}

const LocaleContext = createContext<LocaleContextValue | null>(null)

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() =>
    typeof window === 'undefined' ? 'en' : readStoredLocale(),
  )

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    persistLocale(next)
  }, [])

  const t = useCallback(
    (key: PortalDictKey) => dictionaries[locale][key] ?? dictionaries.en[key] ?? key,
    [locale],
  )

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t])

  return createElement(LocaleContext.Provider, { value }, children)
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext)
  if (!ctx) {
    throw new Error('useLocale must be used within LocaleProvider')
  }
  return ctx
}

export function getPortalDictionary(locale: Locale): Dictionary {
  return dictionaries[locale]
}
