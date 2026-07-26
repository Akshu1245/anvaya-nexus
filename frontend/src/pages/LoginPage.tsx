import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { m3Api } from '../api/m3'

// CDN URLs for real KSP assets
const KSP_LOGO = '/ksp_logo_real.png'
const KAR_EMBLEM = '/kar_main_logo.png'

export function LoginPage() {
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)
  const [officerId, setOfficerId] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    const trimmedId = officerId.trim()
    if (!trimmedId) { setError('Please enter your Officer ID.'); return }
    if (!password) { setError('Please enter your password.'); return }
    setBusy(true); setError('')
    try {
      const user = await m3Api.login(trimmedId, password)
      setUser(user)
      navigate('/app', { replace: true })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8', fontFamily: "'Inter', sans-serif" }}>

      {/* Tricolour */}
      <div className="flex h-1.5 w-full shrink-0">
        <div className="flex-1" style={{ background: '#FF9933' }} />
        <div className="flex-1 bg-white border-y border-gray-200" />
        <div className="flex-1" style={{ background: '#138808' }} />
      </div>

      {/* GOK utility bar */}
      <div style={{ background: '#003087', borderBottom: '1px solid #002070' }} className="px-4 py-1 flex items-center justify-between">
        <span className="text-xs text-blue-200 flex items-center gap-1">
          <span className="material-icons-outlined" style={{ fontSize: 12 }}>language</span>
          Government of Karnataka — Official Portal
        </span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-blue-300" style={{ fontFamily: "'Noto Sans Kannada', sans-serif" }}>ಕರ್ನಾಟಕ ಸರ್ಕಾರ</span>
          <span className="flex items-center gap-1 text-xs text-blue-300">
            <span className="material-icons-outlined" style={{ fontSize: 13 }}>emergency</span>
            112
          </span>
        </div>
      </div>

      {/* KSP Header */}
      <header style={{ background: '#003087', borderBottom: '3px solid #c8a84b' }}>
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center gap-5">
          <img src={KAR_EMBLEM} alt="Karnataka State Emblem" className="h-16 w-auto object-contain hidden md:block shrink-0"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
          <img src={KSP_LOGO} alt="Karnataka State Police" className="h-16 w-16 object-contain rounded-full shrink-0"
            style={{ background: '#fff', border: '2px solid #c8a84b' }}
            onError={(e) => { (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%23003087" stroke="%23c8a84b" stroke-width="4"/><text x="50" y="60" text-anchor="middle" fill="white" font-size="28" font-weight="bold">KSP</text></svg>' }} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold tracking-widest uppercase" style={{ color: '#c8a84b' }}>Government of Karnataka</p>
            <h1 className="text-xl md:text-2xl font-bold text-white">Karnataka State Police</h1>
            <p className="text-xs mt-0.5" style={{ color: '#93b8e8', fontFamily: "'Noto Sans Kannada', sans-serif" }}>
              ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್ — ANVAYA Intelligence Portal
            </p>
          </div>
          <div className="hidden lg:flex flex-col items-end gap-1">
            <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded"
              style={{ background: 'rgba(200,168,75,0.15)', color: '#c8a84b', border: '1px solid rgba(200,168,75,0.3)' }}>
              <span className="material-icons-outlined" style={{ fontSize: 13 }}>lock</span>
              RESTRICTED ACCESS
            </span>
            <span className="text-[10px]" style={{ color: '#6b8ab0' }}>Authorised Personnel Only</span>
          </div>
        </div>
      </header>

      {/* Info bar */}
      <div style={{ background: '#002070', borderBottom: '1px solid rgba(200,168,75,0.2)' }} className="py-1.5 px-4 flex items-center gap-2">
        <span className="material-icons-outlined shrink-0" style={{ fontSize: 13, color: '#c8a84b' }}>info</span>
        <p className="text-xs" style={{ color: '#93b8e8' }}>
          Use your Government-issued <strong className="text-blue-200">Officer ID</strong> (e.g. KSP/BLR/INV/0042) and your registered password to sign in.
          New officer? <Link to="/auth/register" className="underline text-blue-300 hover:text-white">Register here</Link>.
        </p>
      </div>

      {/* Login form */}
      <div className="flex flex-1 items-center justify-center px-4 py-10"
        style={{ background: 'linear-gradient(160deg, #e8edf5 0%, #f0f4f8 100%)' }}>
        <div className="w-full max-w-md">

          <div className="rounded-xl overflow-hidden shadow-xl bg-white" style={{ border: '1px solid #d0d9e8' }}>

            {/* Card header */}
            <div className="px-6 pt-5 pb-4 flex items-center gap-4"
              style={{ background: '#003087', borderBottom: '3px solid #c8a84b' }}>
              <img src={KSP_LOGO} alt="KSP" className="h-11 w-11 object-contain rounded-full shrink-0"
                style={{ background: '#fff', border: '2px solid #c8a84b' }}
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
              <div>
                <h2 className="text-base font-bold text-white">Officer Sign-In</h2>
                <p className="text-xs" style={{ color: '#93b8e8' }}>ANVAYA Investigation Portal — KSP Authorised Use Only</p>
              </div>
            </div>

            <div className="px-6 py-5">
              {error && (
                <div role="alert" className="mb-4 rounded-lg px-4 py-3 text-sm flex items-start gap-2"
                  style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626' }}>
                  <span className="material-icons-outlined text-base shrink-0">error_outline</span>
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-4">
                {/* Officer ID */}
                <div>
                  <label htmlFor="officer-id" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                    <span className="material-icons-outlined" style={{ fontSize: 14 }}>badge</span>
                    Government Officer ID *
                  </label>
                  <input
                    id="officer-id" type="text" value={officerId}
                    onChange={(e) => setOfficerId(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') void handleLogin() }}
                    placeholder="KSP/BLR/INV/0042"
                    autoComplete="username" autoFocus
                    className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all font-mono"
                    style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#f8fafd' }}
                    onFocus={(e) => e.target.style.borderColor = '#003087'}
                    onBlur={(e) => e.target.style.borderColor = '#d0d9e8'}
                  />
                  <p className="mt-1 text-[10px] text-slate-400">Format: KSP/&lt;DISTRICT&gt;/&lt;ROLE&gt;/&lt;NUMBER&gt;</p>
                </div>

                {/* Password */}
                <div>
                  <label htmlFor="login-password" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                    <span className="material-icons-outlined" style={{ fontSize: 14 }}>lock</span>
                    Password *
                  </label>
                  <div className="relative">
                    <input
                      id="login-password" type={showPwd ? 'text' : 'password'} value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') void handleLogin() }}
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all pr-10"
                      style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#f8fafd' }}
                      onFocus={(e) => e.target.style.borderColor = '#003087'}
                      onBlur={(e) => e.target.style.borderColor = '#d0d9e8'}
                    />
                    <button type="button" onClick={() => setShowPwd(!showPwd)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      aria-label={showPwd ? 'Hide password' : 'Show password'}>
                      <span className="material-icons-outlined" style={{ fontSize: 18 }}>
                        {showPwd ? 'visibility_off' : 'visibility'}
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Submit */}
              <button type="button" onClick={() => void handleLogin()} disabled={busy}
                className="mt-6 w-full flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-bold tracking-wide transition-all disabled:cursor-not-allowed disabled:opacity-50"
                style={{ background: busy ? '#1a4080' : '#003087', color: '#fff', boxShadow: '0 4px 14px rgba(0,48,135,0.3)' }}>
                {busy ? (
                  <><svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                  </svg>Signing in…</>
                ) : (
                  <><span className="material-icons-outlined" style={{ fontSize: 18 }}>login</span>Sign In</>
                )}
              </button>

              {/* Register link */}
              <div className="mt-4 flex items-center justify-between">
                <Link to="/auth/register"
                  className="flex items-center gap-1 text-xs font-medium transition-colors"
                  style={{ color: '#003087' }}>
                  <span className="material-icons-outlined" style={{ fontSize: 14 }}>person_add</span>
                  New Officer? Register
                </Link>
                <p className="text-[10px] text-slate-400">IT Act 2000 applies</p>
              </div>
            </div>
          </div>

          {/* Demo hint */}
          <div className="mt-4 rounded-xl px-4 py-3 text-xs" style={{ background: '#fffbeb', border: '1px solid #fde68a', color: '#92400e' }}>
            <p className="font-semibold flex items-center gap-1.5">
              <span className="material-icons-outlined" style={{ fontSize: 14 }}>info</span>
              Demo Credentials
            </p>
            <p className="mt-1">Officer ID: <code className="font-mono bg-amber-100 px-1 rounded">investigator.demo</code> &nbsp; Password: <code className="font-mono bg-amber-100 px-1 rounded">ANVAYA-DEMO-ONLY-2026</code></p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer style={{ background: '#003087', borderTop: '2px solid #c8a84b' }}>
        <div className="flex h-1.5 w-full">
          <div className="flex-1" style={{ background: '#FF9933' }} />
          <div className="flex-1 bg-white" />
          <div className="flex-1" style={{ background: '#138808' }} />
        </div>
        <div className="mx-auto max-w-5xl px-6 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <img src={KSP_LOGO} alt="KSP" className="h-8 w-8 object-contain rounded-full" style={{ background: '#fff' }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
            <div>
              <p className="text-xs font-semibold text-white">Karnataka State Police</p>
              <p className="text-[10px] text-blue-300">© 2026 · KSP Datathon Prototype · Synthetic Data Only</p>
            </div>
          </div>
          <span className="text-[10px] text-blue-400">ANVAYA Nexus v2.0</span>
        </div>
      </footer>
    </div>
  )
}
