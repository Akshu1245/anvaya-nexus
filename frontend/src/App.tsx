import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LocaleProvider } from './i18n/portal'
import { useAuthStore } from './stores/authStore'
import { m3Api } from './api/m3'
import { AuthenticatedLayout } from './components/AuthenticatedLayout'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { DashboardPage } from './pages/DashboardPage'
import { SearchPage } from './pages/SearchPage'
import { WorkspacePage } from './pages/WorkspacePage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { ReportsPage } from './pages/ReportsPage'
import { SupervisorPage } from './pages/SupervisorPage'
import { HealthPage } from './pages/HealthPage'
import { SettingsPage } from './pages/SettingsPage'
import { AppShell } from './app/AppShell'
import { AIHome } from './app/AIHome'
import { DashboardView } from './features/dashboard/DashboardView'
import { CaseDetailView } from './features/case/CaseDetailView'
import { WorkspaceView } from './features/investigation/WorkspaceView'
import { AnalyticsView } from './features/analytics/AnalyticsView'
import { ReportsView } from './features/reports/ReportsView'
import { SupervisorView } from './features/supervisor/SupervisorView'
import { SettingsView } from './features/settings/SettingsView'
import { EvidenceView } from './features/evidence/EvidenceView'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((s) => s.user)

  // Public routes — never fire a session check, avoids 401 noise
  const PUBLIC_PATHS = ['/', '/auth/login', '/auth/register']
  const isPublic = PUBLIC_PATHS.includes(location.pathname)

  useEffect(() => {
    if (isPublic) return          // skip on public routes
    if (user) return              // already authenticated
    m3Api.session()
      .then((sessionUser) => {
        if (sessionUser) {
          useAuthStore.getState().setUser(sessionUser)
        } else {
          navigate('/auth/login', { replace: true })
        }
      })
      .catch(() => {
        navigate('/auth/login', { replace: true })
      })
  }, [user, navigate, isPublic])

  if (!user) {
    // Show a branded loading spinner while checking session
    return (
      <div className="min-h-screen flex items-center justify-center"
        style={{ background: '#003087' }}>
        <div className="flex flex-col items-center gap-4">
          <img
            src="/ksp_logo_real.png"
            alt="KSP"
            className="h-16 w-16 object-contain rounded-full animate-pulse"
            style={{ background: '#fff', border: '2px solid #c8a84b' }}
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
          <div className="h-1 w-24 rounded-full overflow-hidden" style={{ background: 'rgba(200,168,75,0.3)' }}>
            <div className="h-full rounded-full animate-pulse" style={{ background: '#c8a84b', width: '60%' }} />
          </div>
          <p className="text-xs" style={{ color: '#93b8e8' }}>Authenticating…</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/register" element={<RegisterPage />} />

      {/* Authenticated — /app routes using AppShell */}
      <Route path="/onboarding" element={<AuthGuard><OnboardingPage /></AuthGuard>} />
      <Route path="/app" element={<AuthGuard><AppShell><AIHome /></AppShell></AuthGuard>} />
      <Route path="/app/home" element={<AuthGuard><AppShell><AIHome /></AppShell></AuthGuard>} />
      <Route path="/app/chat/:id" element={<AuthGuard><AppShell><AIHome /></AppShell></AuthGuard>} />
      <Route path="/app/dashboard" element={<AuthGuard><AppShell><DashboardView /></AppShell></AuthGuard>} />
      <Route path="/app/cases/:id" element={<AuthGuard><AppShell><CaseDetailView /></AppShell></AuthGuard>} />
      <Route path="/app/workspace/:id" element={<AuthGuard><AppShell><WorkspaceView /></AppShell></AuthGuard>} />
      <Route path="/app/analytics" element={<AuthGuard><AppShell><AnalyticsView /></AppShell></AuthGuard>} />
      <Route path="/app/reports" element={<AuthGuard><AppShell><ReportsView /></AppShell></AuthGuard>} />
      <Route path="/app/supervisor" element={<AuthGuard><AppShell><SupervisorView /></AppShell></AuthGuard>} />
      <Route path="/app/settings" element={<AuthGuard><AppShell><SettingsView /></AppShell></AuthGuard>} />
      <Route path="/app/evidence" element={<AuthGuard><AppShell><EvidenceView /></AppShell></AuthGuard>} />
      <Route path="/app/search" element={<AuthGuard><AppShell><AIHome /></AppShell></AuthGuard>} />

      {/* Legacy /dashboard routes using AuthenticatedLayout */}
      <Route path="/dashboard" element={<AuthGuard><AuthenticatedLayout><DashboardPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/search" element={<AuthGuard><AuthenticatedLayout><SearchPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/workspace" element={<AuthGuard><AuthenticatedLayout><WorkspacePage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/cases/:id" element={<AuthGuard><AuthenticatedLayout><CaseDetailPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/analytics" element={<AuthGuard><AuthenticatedLayout><AnalyticsPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/reports" element={<AuthGuard><AuthenticatedLayout><ReportsPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/supervisor" element={<AuthGuard><AuthenticatedLayout><SupervisorPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/health" element={<AuthGuard><AuthenticatedLayout><HealthPage /></AuthenticatedLayout></AuthGuard>} />
      <Route path="/dashboard/settings" element={<AuthGuard><AuthenticatedLayout><SettingsPage /></AuthenticatedLayout></AuthGuard>} />

      {/* Common short aliases — redirect to real /app/* routes with auth */}
      <Route path="/evidence" element={<Navigate to="/app/evidence" replace />} />
      <Route path="/chat" element={<Navigate to="/app" replace />} />
      <Route path="/analytics" element={<Navigate to="/app/analytics" replace />} />
      <Route path="/cases" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/cases/:id" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/admin" element={<Navigate to="/app/supervisor" replace />} />
      <Route path="/profile" element={<Navigate to="/app/settings" replace />} />
      <Route path="/settings" element={<Navigate to="/app/settings" replace />} />
      <Route path="/reports" element={<Navigate to="/app/reports" replace />} />
      <Route path="/register" element={<Navigate to="/auth/register" replace />} />

      {/* 404 catch-all */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export function App() {
  return (
    <ErrorBoundary>
      <LocaleProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </LocaleProvider>
    </ErrorBoundary>
  )
}
