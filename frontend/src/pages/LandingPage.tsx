import { Link } from 'react-router-dom'
import { useLocale } from '../i18n/portal'

// SVG fallback badges (shown if local images fail to load)
const KSP_BADGE_SVG = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="%23003087" stroke="%23c8a84b" stroke-width="4"/><text x="50" y="44" text-anchor="middle" fill="%23c8a84b" font-family="Arial" font-size="11" font-weight="bold">ಕೆಎಸ್‌ಪಿ</text><text x="50" y="60" text-anchor="middle" fill="white" font-family="Arial" font-size="13" font-weight="bold">KSP</text><text x="50" y="74" text-anchor="middle" fill="%23c8a84b" font-family="Arial" font-size="8">KARNATAKA</text></svg>')}`
const KAR_EMBLEM_SVG = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="8" fill="%23f8f4e8"/><circle cx="50" cy="38" r="22" fill="none" stroke="%23003087" stroke-width="3"/><text x="50" y="44" text-anchor="middle" fill="%23003087" font-family="Arial" font-size="9" font-weight="bold">KARNATAKA</text><text x="50" y="68" text-anchor="middle" fill="%23003087" font-family="Arial" font-size="8">GOVT</text></svg>')}`

const socialLinks = [
  { label: 'KSP Official Website', href: 'https://ksp.karnataka.gov.in', icon: 'language' },
  { label: 'Karnataka Government', href: 'https://karnataka.gov.in', icon: 'account_balance' },
  { label: 'Emergency 112', href: 'tel:112', icon: 'emergency' },
]

const navLinks = [
  { label: 'Home', href: '#hero' },
  { label: 'About KSP', href: '#about' },
  { label: 'ANVAYA Portal', href: '/auth/login' },
  { label: 'FIR Analytics', href: '#features' },
  { label: 'Crime Statistics', href: '#stats' },
  { label: 'Contact', href: '#contact' },
]

const stats = [
  { value: '12,000+', label: 'FIRs in Dataset', icon: 'folder_open' },
  { value: '38', label: 'Districts Covered', icon: 'map' },
  { value: '1,200+', label: 'Police Stations', icon: 'local_police' },
  { value: '99.9%', label: 'System Uptime', icon: 'check_circle' },
]

const features = [
  {
    icon: 'manage_search',
    title: 'AI FIR Search',
    titleKn: 'ಎಐ FIR ಹುಡುಕಾಟ',
    desc: 'Natural language queries across CCTNS-replica FIR records. Ask in English or Kannada.',
    route: '/app',
    routeLabel: 'Open AI Chat',
  },
  {
    icon: 'analytics',
    title: 'Crime Analytics',
    titleKn: 'ಅಪರಾಧ ವಿಶ್ಲೇಷಣೆ',
    desc: 'District-wise trends, offence heatmaps, and shift intelligence for operational planning.',
    route: '/app/analytics',
    routeLabel: 'View Analytics',
  },
  {
    icon: 'description',
    title: 'Case Dossiers',
    titleKn: 'ಪ್ರಕರಣ ದೋಷಿಪತ್ರ',
    desc: 'Automated Case 360 reports with cited sources, suspect timelines, and evidence chain.',
    route: '/app/dashboard',
    routeLabel: 'View Dashboard',
  },
  {
    icon: 'inventory_2',
    title: 'Evidence Repository',
    titleKn: 'ಸಾಕ್ಷ್ಯ ಭಂಡಾರ',
    desc: 'Track physical, digital, and forensic evidence with full chain-of-custody audit trail.',
    route: '/app/evidence',
    routeLabel: 'Open Evidence',
  },
  {
    icon: 'supervisor_account',
    title: 'Supervisor Review',
    titleKn: 'ಮೇಲ್ವಿಚಾರಕ ವಿಮರ್ಶೆ',
    desc: 'SHO-level review dashboard for officer activity, shift briefings, and case prioritisation.',
    route: '/app/supervisor',
    routeLabel: 'Supervisor View',
  },
  {
    icon: 'summarize',
    title: 'PDF Reports',
    titleKn: 'ಪಿಡಿಎಫ್ ವರದಿಗಳು',
    desc: 'Auto-generated, source-cited PDF investigation briefs ready for court or departmental use.',
    route: '/app/reports',
    routeLabel: 'View Reports',
  },
]

export function LandingPage() {
  const { locale, setLocale } = useLocale()

  return (
    <div className="min-h-screen flex flex-col" style={{ fontFamily: "'Inter', sans-serif", background: '#f0f4f8' }}>

      {/* Tricolour top bar */}
      <div className="flex h-1.5 w-full shrink-0">
        <div className="flex-1" style={{ background: '#FF9933' }} />
        <div className="flex-1 bg-white" />
        <div className="flex-1" style={{ background: '#138808' }} />
      </div>

      {/* GOK utility bar */}
      <div style={{ background: '#002060', borderBottom: '1px solid rgba(200,168,75,0.3)' }}
        className="px-4 py-1 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <a href="https://karnataka.gov.in" target="_blank" rel="noopener"
            className="text-xs flex items-center gap-1 text-blue-300 hover:text-white transition-colors">
            <span className="material-icons-outlined" style={{ fontSize: 12 }}>language</span>
            Government of Karnataka
          </a>
          <span className="text-blue-700 text-xs">|</span>
          <a href="https://ksp.karnataka.gov.in" target="_blank" rel="noopener"
            className="text-xs text-blue-400 hover:text-white transition-colors">
            ksp.karnataka.gov.in
          </a>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setLocale(locale === 'en' ? 'kn' : 'en')}
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold transition-all"
            style={{
              background: '#c8a84b',
              color: '#001f5c',
            }}>
            <span className="material-icons-outlined" style={{ fontSize: 13 }}>translate</span>
            {locale === 'en' ? 'ಕನ್ನಡ' : 'English'}
          </button>
          {socialLinks.map((s) => (
            <a key={s.label} href={s.href} target={s.href.startsWith('http') ? '_blank' : undefined}
              rel="noopener" className="flex items-center gap-1 text-xs text-blue-400 hover:text-white transition-colors" title={s.label}>
              <span className="material-icons-outlined" style={{ fontSize: 13 }}>{s.icon}</span>
            </a>
          ))}
        </div>
      </div>

      {/* ── Header ── */}
      <header style={{ background: '#003087', borderBottom: '3px solid #c8a84b' }}>
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center gap-5">
          <img src="/kar_main_logo.png" alt="Karnataka State Emblem"
            className="h-16 w-auto object-contain hidden md:block shrink-0"
            onError={(e) => { (e.target as HTMLImageElement).src = KAR_EMBLEM_SVG }} />
          <img src="/ksp_logo_real.png" alt="Karnataka State Police Badge"
            className="h-16 w-16 object-contain rounded-full shrink-0"
            style={{ background: '#fff', border: '2px solid #c8a84b', boxShadow: '0 0 12px rgba(200,168,75,0.3)' }}
            onError={(e) => { (e.target as HTMLImageElement).src = KSP_BADGE_SVG }} />
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold tracking-widest uppercase" style={{ color: '#c8a84b' }}>
              Government of Karnataka · ಕರ್ನಾಟಕ ಸರ್ಕಾರ
            </p>
            <h1 className="text-2xl md:text-3xl font-bold text-white">Karnataka State Police</h1>
            <p className="text-xs mt-0.5" style={{ color: '#93b8e8' }}>
              ANVAYA Investigation Intelligence Portal — Datathon 2026 Prototype
            </p>
            <p className="text-xs mt-0.5" style={{ color: '#5a7a9a', fontFamily: "'Noto Sans Kannada', sans-serif" }}>
              ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ — ಅನ್ವಯ ತನಿಖಾ ಪೋರ್ಟಲ್
            </p>
          </div>
          <div className="hidden lg:flex flex-col items-end gap-2">
            <a href="tel:112" className="flex items-center gap-1 text-sm font-bold" style={{ color: '#c8a84b' }}>
              <span className="material-icons-outlined" style={{ fontSize: 16 }}>emergency</span>
              Emergency: 112
            </a>
            <span className="text-[10px]" style={{ color: '#4a6080' }}>24×7 Police Helpline</span>
          </div>
        </div>

        {/* Sub-navigation */}
        <div style={{ background: 'rgba(0,0,0,0.25)', borderTop: '1px solid rgba(200,168,75,0.2)' }}>
          <div className="mx-auto max-w-7xl px-6 flex items-center overflow-x-auto">
            {navLinks.map((item, i) => (
              <a key={item.label} href={item.href}
                className="px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-all border-b-2"
                style={{
                  color: i === 2 ? '#c8a84b' : '#93b8e8',
                  borderBottomColor: i === 2 ? '#c8a84b' : 'transparent',
                }}>
                {item.label}
              </a>
            ))}
            <div className="ml-auto">
              <Link to="/auth/login" className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-bold transition-all" style={{ color: '#c8a84b' }}>
                <span className="material-icons-outlined" style={{ fontSize: 14 }}>login</span>
                Officer Login
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* ── Hero ── */}
      <section id="hero" style={{ background: 'linear-gradient(160deg, #001f5c 0%, #003087 60%, #001f5c 100%)' }} className="py-16 px-6">
        <div className="mx-auto max-w-7xl flex flex-col lg:flex-row items-center gap-12">
          <div className="flex-1 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold mb-5"
              style={{ background: 'rgba(200,168,75,0.15)', border: '1px solid rgba(200,168,75,0.4)', color: '#c8a84b' }}>
              <span className="material-icons-outlined" style={{ fontSize: 14 }}>verified</span>
              Official Police Intelligence Platform
            </div>
            <h2 className="text-3xl md:text-4xl font-black text-white leading-tight">
              ANVAYA<br />
              <span style={{ color: '#c8a84b' }}>Investigation</span><br />
              Intelligence
            </h2>
            <p className="mt-4 text-sm leading-relaxed max-w-lg" style={{ color: '#6b8ab0' }}>
              AI-powered investigation assistant for Karnataka State Police. Search FIR records,
              generate case dossiers, analyse crime trends — all with cited, auditable sources.
            </p>
            <p className="mt-2 text-xs" style={{ color: '#3a5070', fontFamily: "'Noto Sans Kannada', sans-serif" }}>
              ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಆಧಾರಿತ ತನಿಖಾ ಸಹಾಯಕ
            </p>
            <div className="mt-8 flex flex-wrap gap-4 justify-center lg:justify-start">
              <Link to="/auth/login"
                className="flex items-center gap-2 px-6 py-3 rounded-lg font-bold text-sm transition-all"
                style={{ background: '#c8a84b', color: '#001f5c', boxShadow: '0 4px 20px rgba(200,168,75,0.4)' }}>
                <span className="material-icons-outlined" style={{ fontSize: 18 }}>login</span>
                Officer Sign In
              </Link>
              <a href="#features"
                className="flex items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all"
                style={{ border: '1px solid rgba(200,168,75,0.4)', color: '#c8a84b' }}>
                <span className="material-icons-outlined" style={{ fontSize: 18 }}>explore</span>
                Explore Features
              </a>
            </div>
          </div>

          {/* Hero badge panel */}
          <div className="shrink-0 flex flex-col items-center gap-4">
            <div className="rounded-2xl p-8 flex flex-col items-center gap-4"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(200,168,75,0.2)' }}>
              <img src="/ksp_logo_real.png" alt="Karnataka State Police"
                className="h-28 w-28 object-contain rounded-full"
                style={{ background: '#fff', border: '3px solid #c8a84b', boxShadow: '0 0 30px rgba(200,168,75,0.3)' }}
                onError={(e) => { (e.target as HTMLImageElement).src = KSP_BADGE_SVG }} />
              <img src="/kar_main_logo.png" alt="Karnataka State Emblem"
                className="h-16 w-auto object-contain opacity-80"
                onError={(e) => { (e.target as HTMLImageElement).src = KAR_EMBLEM_SVG }} />
              <p className="text-xs font-semibold text-center" style={{ color: '#c8a84b' }}>
                Karnataka State Police<br />
                <span style={{ color: '#4a6a90', fontFamily: "'Noto Sans Kannada', sans-serif", fontSize: 11 }}>ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <div id="stats" style={{ background: '#c8a84b' }}>
        <div className="mx-auto max-w-7xl px-6 py-3 grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s) => (
            <div key={s.label} className="flex items-center gap-3">
              <span className="material-icons-outlined text-2xl" style={{ color: '#001f5c' }}>{s.icon}</span>
              <div>
                <p className="text-lg font-bold" style={{ color: '#001f5c' }}>{s.value}</p>
                <p className="text-xs font-semibold" style={{ color: '#3a3010' }}>{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Features ── */}
      <section id="features" className="py-16 px-6" style={{ background: '#f8f9fb' }}>
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-12">
            <p className="text-xs font-bold tracking-widest uppercase mb-2" style={{ color: '#003087' }}>Platform Capabilities</p>
            <h3 className="text-2xl font-bold text-slate-800">Investigation Intelligence Features</h3>
            <p className="text-sm mt-1 text-slate-500" style={{ fontFamily: "'Noto Sans Kannada', sans-serif" }}>
              ತನಿಖಾ ಬುದ್ಧಿಮತ್ತೆ ವೈಶಿಷ್ಟ್ಯಗಳು
            </p>
            <div className="mt-3 mx-auto h-0.5 w-20" style={{ background: 'linear-gradient(90deg, transparent, #003087, transparent)' }} />
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="rounded-xl p-6 bg-white transition-all group flex flex-col"
                style={{ border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}
                onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,48,135,0.12)')}
                onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)')}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl mb-4" style={{ background: '#003087' }}>
                  <span className="material-icons-outlined text-white" style={{ fontSize: 24 }}>{f.icon}</span>
                </div>
                <h4 className="font-bold text-slate-800">{f.title}</h4>
                <p className="text-[10px] mt-0.5 font-medium" style={{ color: '#003087', fontFamily: "'Noto Sans Kannada', sans-serif" }}>{f.titleKn}</p>
                <p className="mt-3 text-sm leading-relaxed text-slate-500 flex-1">{f.desc}</p>
                <Link to={f.route}
                  className="mt-4 flex items-center gap-1.5 text-xs font-semibold transition-colors"
                  style={{ color: '#003087' }}>
                  <span className="material-icons-outlined" style={{ fontSize: 14 }}>arrow_forward</span>
                  {f.routeLabel}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── About ── */}
      <section id="about" className="py-12 px-6" style={{ background: '#fff' }}>
        <div className="mx-auto max-w-7xl flex flex-col md:flex-row items-center gap-8">
          <div className="flex-1">
            <p className="text-xs font-bold tracking-widest uppercase mb-2" style={{ color: '#c8a84b' }}>About This Platform</p>
            <h3 className="text-xl font-bold text-slate-800">ANVAYA — Connecting the Dots</h3>
            <p className="mt-3 text-sm leading-relaxed text-slate-500">
              ANVAYA (Sanskrit: connection, linkage) is a synthetic-data investigation intelligence prototype
              built for the <strong>KSP Datathon 2026</strong>. It demonstrates how AI-grounded, source-cited
              answers can assist Investigating Officers without replacing human judgment.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {[
                { label: 'No live CCTNS connection', icon: 'cloud_off' },
                { label: 'Synthetic data only', icon: 'science' },
                { label: 'Source-cited answers', icon: 'verified' },
                { label: 'Human decision-making', icon: 'person' },
              ].map((p) => (
                <div key={p.label} className="flex items-center gap-2 text-xs text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 16, color: '#003087' }}>{p.icon}</span>
                  {p.label}
                </div>
              ))}
            </div>
          </div>
          <div className="shrink-0 flex gap-4 items-center">
            <div className="text-center">
              <img src="/ksp_logo_real.png" alt="KSP" className="h-20 w-20 object-contain rounded-full mx-auto"
                style={{ background: '#003087', border: '3px solid #c8a84b', padding: 8 }}
                onError={(e) => { (e.target as HTMLImageElement).src = KSP_BADGE_SVG }} />
              <p className="text-xs font-semibold mt-2 text-slate-600">KSP</p>
            </div>
            <div className="text-center">
              <img src="/kar_main_logo.png" alt="Karnataka Emblem" className="h-20 w-auto object-contain mx-auto"
                onError={(e) => { (e.target as HTMLImageElement).src = KAR_EMBLEM_SVG }} />
              <p className="text-xs font-semibold mt-2 text-slate-600">Karnataka</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Contact / CTA ── */}
      <section id="contact" style={{ background: '#003087' }} className="py-12 px-6">
        <div className="mx-auto max-w-7xl text-center">
          <h3 className="text-xl font-bold text-white mb-2">Ready to Sign In?</h3>
          <p className="text-sm text-blue-300 mb-6">
            Use your Government-issued Officer ID to access the ANVAYA portal.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/auth/login"
              className="flex items-center gap-2 px-8 py-3 rounded-lg font-bold text-sm"
              style={{ background: '#c8a84b', color: '#001f5c' }}>
              <span className="material-icons-outlined" style={{ fontSize: 18 }}>login</span>
              Officer Sign In
            </Link>
            <Link to="/auth/register"
              className="flex items-center gap-2 px-8 py-3 rounded-lg font-semibold text-sm"
              style={{ border: '1px solid rgba(200,168,75,0.5)', color: '#c8a84b' }}>
              <span className="material-icons-outlined" style={{ fontSize: 18 }}>person_add</span>
              First Time? Register
            </Link>
          </div>
        </div>
      </section>

      {/* ── Disclaimer ── */}
      <section style={{ background: '#001f5c', borderTop: '2px solid #c8a84b' }}>
        <div className="mx-auto max-w-7xl px-6 py-8 flex flex-col md:flex-row items-center gap-6">
          <div className="flex items-center gap-3 shrink-0">
            <span className="material-icons-outlined text-3xl" style={{ color: '#c8a84b' }}>warning_amber</span>
            <p className="font-bold text-sm" style={{ color: '#c8a84b' }}>Important Disclaimer</p>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: '#6b8ab0' }}>
            This is a <strong className="text-blue-200">synthetic data prototype</strong> for the KSP Datathon 2026.
            No source, no factual claim. ANVAYA has <strong className="text-blue-200">no live KSP/CCTNS connection</strong> and
            makes no identity, guilt, risk, or operational decision. Authorised personnel only.
            Unauthorised access is punishable under IT Act 2000.
          </p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ background: '#001040', borderTop: '1px solid rgba(200,168,75,0.2)' }}>
        <div className="flex h-1.5 w-full">
          <div className="flex-1" style={{ background: '#FF9933' }} />
          <div className="flex-1 bg-white" />
          <div className="flex-1" style={{ background: '#138808' }} />
        </div>
        <div className="mx-auto max-w-7xl px-6 py-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/ksp_logo_real.png" alt="KSP" className="h-10 w-10 object-contain rounded-full"
              style={{ background: '#fff', border: '1px solid rgba(200,168,75,0.4)' }}
              onError={(e) => { (e.target as HTMLImageElement).src = KSP_BADGE_SVG }} />
            <div>
              <p className="text-xs font-semibold text-white">Karnataka State Police</p>
              <p className="text-[10px] text-blue-400">© 2026 · KSP Datathon Prototype · Synthetic Data Only · v2.0</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {['Privacy Policy', 'Terms of Use', 'Accessibility', 'Help'].map((link) => (
              <a key={link} href="#" className="text-[10px] text-blue-500 hover:text-blue-300 hover:underline">{link}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
