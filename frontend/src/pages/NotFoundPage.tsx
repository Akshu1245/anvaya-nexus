import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

const KSP_BADGE_SVG = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="%23003087" stroke="%23c8a84b" stroke-width="4"/><text x="50" y="44" text-anchor="middle" fill="%23c8a84b" font-family="Arial" font-size="11" font-weight="bold">ಕೆಎಸ್\u200cಪಿ</text><text x="50" y="60" text-anchor="middle" fill="white" font-family="Arial" font-size="13" font-weight="bold">KSP</text><text x="50" y="74" text-anchor="middle" fill="%23c8a84b" font-family="Arial" font-size="8">KARNATAKA</text></svg>')}`

export function NotFoundPage() {
  const user = useAuthStore((s) => s.user)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ background: 'linear-gradient(160deg, #001f5c 0%, #003087 100%)', fontFamily: "'Inter', sans-serif" }}>

      {/* Tricolour top */}
      <div className="fixed top-0 left-0 right-0 flex h-1.5">
        <div className="flex-1" style={{ background: '#FF9933' }} />
        <div className="flex-1 bg-white" />
        <div className="flex-1" style={{ background: '#138808' }} />
      </div>

      <div className="text-center max-w-md">
        {/* KSP logo */}
        <img src="/ksp_logo_real.png" alt="KSP" className="h-20 w-20 object-contain rounded-full mx-auto mb-6"
          style={{ background: '#fff', border: '3px solid #c8a84b', boxShadow: '0 0 30px rgba(200,168,75,0.3)', padding: 6 }}
          onError={(e) => { (e.target as HTMLImageElement).src = KSP_BADGE_SVG }} />

        {/* 404 */}
        <div className="mb-4">
          <p className="text-7xl font-black" style={{ color: '#c8a84b' }}>404</p>
          <div className="h-0.5 w-16 mx-auto my-3" style={{ background: '#c8a84b' }} />
          <h1 className="text-xl font-bold text-white">Page Not Found</h1>
          <p className="text-sm mt-1" style={{ color: '#93b8e8' }}>
            The page you are looking for does not exist or has been moved.
          </p>
          <p className="text-xs mt-2" style={{ color: '#4a6080', fontFamily: "'Noto Sans Kannada', 'Noto Sans', sans-serif" }}>
            ಈ ಪುಟ ಅಸ್ತಿತ್ವದಲ್ಲಿಲ್ಲ
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
          {user ? (
            <Link to="/app"
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-bold text-sm"
              style={{ background: '#c8a84b', color: '#001f5c' }}>
              <span className="material-icons-outlined" style={{ fontSize: 18 }}>home</span>
              Go to Portal
            </Link>
          ) : (
            <Link to="/"
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-bold text-sm"
              style={{ background: '#c8a84b', color: '#001f5c' }}>
              <span className="material-icons-outlined" style={{ fontSize: 18 }}>home</span>
              Go to Home
            </Link>
          )}
          <Link to="/auth/login"
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm"
            style={{ border: '1px solid rgba(200,168,75,0.4)', color: '#c8a84b' }}>
            <span className="material-icons-outlined" style={{ fontSize: 18 }}>login</span>
            Officer Login
          </Link>
        </div>

        <p className="mt-8 text-xs" style={{ color: '#2a4060' }}>
          Karnataka State Police · ANVAYA Portal · v2.0
        </p>
      </div>
    </div>
  )
}
