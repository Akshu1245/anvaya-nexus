import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { m3Api } from '../api/m3'

const KSP_LOGO = '/ksp_logo_real.png'
const KAR_EMBLEM = '/kar_main_logo.png'

const roles = [
  { value: 'INVESTIGATOR', label: 'Investigating Officer', labelKn: 'ತನಿಖಾ ಅಧಿಕಾರಿ', icon: 'manage_search' },
  { value: 'CRIME_ANALYST', label: 'Crime Analyst', labelKn: 'ಅಪರಾಧ ವಿಶ್ಲೇಷಕ', icon: 'analytics' },
  { value: 'SUPERVISOR', label: 'Supervisor / SHO', labelKn: 'ಮೇಲ್ವಿಚಾರಕ / SHO', icon: 'supervisor_account' },
]

export function RegisterPage() {
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)

  const [officerId, setOfficerId] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('INVESTIGATOR')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [station, setStation] = useState('')
  const [district, setDistrict] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const validate = () => {
    if (!officerId.trim()) return 'Officer ID is required.'
    if (!fullName.trim()) return 'Full name is required.'
    if (!password) return 'Password is required.'
    if (password.length < 8) return 'Password must be at least 8 characters.'
    if (password !== confirm) return 'Passwords do not match.'
    return null
  }

  const handleRegister = async () => {
    const err = validate()
    if (err) { setError(err); return }
    setBusy(true); setError('')
    try {
      const user = await m3Api.register({
        officer_id: officerId.trim().toUpperCase(),
        full_name: fullName.trim(),
        role,
        password,
        station: station.trim() || undefined,
        district: district.trim() || undefined,
      })
      setUser(user)
      navigate('/app', { replace: true })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const pwdStrength = password.length === 0 ? 0 : password.length < 8 ? 1 : password.length < 12 ? 2 : 3
  const pwdColors = ['', '#ef4444', '#f59e0b', '#22c55e']
  const pwdLabels = ['', 'Weak', 'Fair', 'Strong']

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8', fontFamily: "'Inter', sans-serif" }}>

      {/* Tricolour */}
      <div className="flex h-1.5 w-full shrink-0">
        <div className="flex-1" style={{ background: '#FF9933' }} />
        <div className="flex-1 bg-white border-y border-gray-200" />
        <div className="flex-1" style={{ background: '#138808' }} />
      </div>

      {/* GOK bar */}
      <div style={{ background: '#003087', borderBottom: '1px solid #002070' }} className="px-4 py-1 flex items-center justify-between">
        <span className="text-xs text-blue-200">Government of Karnataka — Official Portal</span>
        <span className="text-xs text-blue-300" style={{ fontFamily: "'Noto Sans Kannada', sans-serif" }}>ಕರ್ನಾಟಕ ಸರ್ಕಾರ</span>
      </div>

      {/* Header */}
      <header style={{ background: '#003087', borderBottom: '3px solid #c8a84b' }}>
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center gap-5">
          <img src={KAR_EMBLEM} alt="Karnataka State Emblem" className="h-14 w-auto object-contain hidden md:block shrink-0"
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
          <img src={KSP_LOGO} alt="KSP" className="h-14 w-14 object-contain rounded-full shrink-0"
            style={{ background: '#fff', border: '2px solid #c8a84b' }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
          <div className="flex-1">
            <p className="text-xs font-bold tracking-widest uppercase" style={{ color: '#c8a84b' }}>Government of Karnataka</p>
            <h1 className="text-xl font-bold text-white">Karnataka State Police — Officer Registration</h1>
            <p className="text-xs mt-0.5" style={{ color: '#93b8e8', fontFamily: "'Noto Sans Kannada', sans-serif" }}>ಅಧಿಕಾರಿ ನೋಂದಣಿ — ANVAYA Intelligence Portal</p>
          </div>
        </div>
      </header>

      {/* Form */}
      <div className="flex flex-1 items-start justify-center px-4 py-10"
        style={{ background: 'linear-gradient(160deg, #e8edf5 0%, #f0f4f8 100%)' }}>
        <div className="w-full max-w-lg">

          <div className="rounded-xl overflow-hidden shadow-xl bg-white" style={{ border: '1px solid #d0d9e8' }}>
            {/* Card header */}
            <div className="px-6 pt-5 pb-4 flex items-center gap-4"
              style={{ background: '#003087', borderBottom: '3px solid #c8a84b' }}>
              <span className="material-icons-outlined text-white" style={{ fontSize: 28 }}>person_add</span>
              <div>
                <h2 className="text-base font-bold text-white">New Officer Registration</h2>
                <p className="text-xs" style={{ color: '#93b8e8' }}>First-time setup using your Government-issued Officer ID</p>
              </div>
            </div>

            <div className="px-6 py-5 space-y-4">
              {error && (
                <div role="alert" className="rounded-lg px-4 py-3 text-sm flex items-start gap-2"
                  style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626' }}>
                  <span className="material-icons-outlined text-base shrink-0">error_outline</span>
                  <span>{error}</span>
                </div>
              )}

              {/* Officer ID */}
              <div>
                <label htmlFor="reg-officer-id" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 13 }}>badge</span>
                  Government Officer ID *
                </label>
                <input id="reg-officer-id" type="text" value={officerId}
                  onChange={(e) => setOfficerId(e.target.value.toUpperCase())}
                  placeholder="KSP/BLR/INV/0042"
                  autoComplete="username" autoFocus
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all font-mono"
                  style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#f8fafd' }}
                  onFocus={(e) => e.target.style.borderColor = '#003087'}
                  onBlur={(e) => e.target.style.borderColor = '#d0d9e8'} />
                <p className="mt-1 text-[10px] text-slate-400">Issued by your Superintendent of Police. Format: KSP/&lt;DISTRICT&gt;/&lt;ROLE_CODE&gt;/&lt;NUMBER&gt;</p>
              </div>

              {/* Full name */}
              <div>
                <label htmlFor="reg-full-name" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 13 }}>person</span>
                  Full Name *
                </label>
                <input id="reg-full-name" type="text" value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ravi Kumar"
                  autoComplete="name"
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all"
                  style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#f8fafd' }}
                  onFocus={(e) => e.target.style.borderColor = '#003087'}
                  onBlur={(e) => e.target.style.borderColor = '#d0d9e8'} />
              </div>

              {/* Role */}
              <div>
                <label className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 13 }}>work</span>
                  Designation / Role *
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {roles.map((r) => (
                    <label key={r.value} className="flex flex-col items-center gap-1 rounded-lg p-2.5 cursor-pointer transition-all text-center"
                      style={{
                        border: role === r.value ? '1.5px solid #003087' : '1.5px solid #d0d9e8',
                        background: role === r.value ? '#eff4ff' : '#fafbfd',
                      }}>
                      <input type="radio" name="role" value={r.value} checked={role === r.value}
                        onChange={() => setRole(r.value)} className="sr-only" />
                      <span className="material-icons-outlined" style={{ fontSize: 22, color: role === r.value ? '#003087' : '#94a3b8' }}>{r.icon}</span>
                      <span className="text-[11px] font-semibold" style={{ color: role === r.value ? '#003087' : '#1e293b' }}>{r.label}</span>
                      <span className="text-[9px]" style={{ color: '#94a3b8', fontFamily: "'Noto Sans Kannada', sans-serif" }}>{r.labelKn}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="reg-password" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 13 }}>lock</span>
                  Create Password *
                </label>
                <div className="relative">
                  <input id="reg-password" type={showPwd ? 'text' : 'password'} value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    autoComplete="new-password"
                    className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all pr-10"
                    style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#f8fafd' }}
                    onFocus={(e) => e.target.style.borderColor = '#003087'}
                    onBlur={(e) => e.target.style.borderColor = '#d0d9e8'} />
                  <button type="button" onClick={() => setShowPwd(!showPwd)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                    <span className="material-icons-outlined" style={{ fontSize: 18 }}>{showPwd ? 'visibility_off' : 'visibility'}</span>
                  </button>
                </div>
                {/* Strength meter */}
                {password.length > 0 && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="flex gap-1 flex-1">
                      {[1,2,3].map((i) => (
                        <div key={i} className="h-1 flex-1 rounded-full transition-all"
                          style={{ background: i <= pwdStrength ? pwdColors[pwdStrength] : '#e2e8f0' }} />
                      ))}
                    </div>
                    <span className="text-[10px] font-medium" style={{ color: pwdColors[pwdStrength] }}>{pwdLabels[pwdStrength]}</span>
                  </div>
                )}
              </div>

              {/* Confirm password */}
              <div>
                <label htmlFor="reg-confirm" className="flex items-center gap-1.5 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                  <span className="material-icons-outlined" style={{ fontSize: 13 }}>lock_check</span>
                  Confirm Password *
                </label>
                <input id="reg-confirm" type={showPwd ? 'text' : 'password'} value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleRegister() }}
                  placeholder="Re-enter password"
                  autoComplete="new-password"
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-all"
                  style={{
                    border: `1.5px solid ${confirm && confirm !== password ? '#fca5a5' : '#d0d9e8'}`,
                    color: '#1a1a2e', background: '#f8fafd'
                  }}
                  onFocus={(e) => e.target.style.borderColor = confirm !== password ? '#fca5a5' : '#003087'}
                  onBlur={(e) => e.target.style.borderColor = confirm && confirm !== password ? '#fca5a5' : '#d0d9e8'} />
                {confirm && confirm !== password && (
                  <p className="mt-1 text-[10px] text-red-500">Passwords do not match</p>
                )}
              </div>

              {/* Station + District */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="reg-station" className="flex items-center gap-1 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                    <span className="material-icons-outlined" style={{ fontSize: 12 }}>location_city</span>
                    Station <span className="text-slate-400 font-normal normal-case">(opt.)</span>
                  </label>
                  <input id="reg-station" type="text" value={station}
                    onChange={(e) => setStation(e.target.value)} placeholder="Jayanagar PS"
                    className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
                    style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#fafbfd' }} />
                </div>
                <div>
                  <label htmlFor="reg-district" className="flex items-center gap-1 text-xs font-semibold mb-1.5 uppercase tracking-wider text-slate-600">
                    <span className="material-icons-outlined" style={{ fontSize: 12 }}>map</span>
                    District <span className="text-slate-400 font-normal normal-case">(opt.)</span>
                  </label>
                  <input id="reg-district" type="text" value={district}
                    onChange={(e) => setDistrict(e.target.value)} placeholder="Bengaluru"
                    className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
                    style={{ border: '1.5px solid #d0d9e8', color: '#1a1a2e', background: '#fafbfd' }} />
                </div>
              </div>

              {/* Submit */}
              <button type="button" onClick={() => void handleRegister()} disabled={busy}
                className="w-full flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-bold tracking-wide transition-all disabled:cursor-not-allowed disabled:opacity-50"
                style={{ background: busy ? '#1a4080' : '#003087', color: '#fff', boxShadow: '0 4px 14px rgba(0,48,135,0.3)' }}>
                {busy ? (
                  <><svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                  </svg>Registering…</>
                ) : (
                  <><span className="material-icons-outlined" style={{ fontSize: 18 }}>how_to_reg</span>Register & Sign In</>
                )}
              </button>

              <div className="flex items-center justify-between mt-2">
                <Link to="/auth/login" className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors">
                  <span className="material-icons-outlined" style={{ fontSize: 14 }}>arrow_back</span>
                  Already registered? Sign In
                </Link>
                <p className="text-[10px] text-slate-400">IT Act 2000 applies</p>
              </div>
            </div>
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
        <div className="mx-auto max-w-5xl px-6 py-3 flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-white">Karnataka State Police — ANVAYA Portal</p>
          <p className="text-[10px] text-blue-400">© 2026 · KSP Datathon Prototype · Synthetic Data Only</p>
        </div>
      </footer>
    </div>
  )
}
