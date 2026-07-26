import { useCallback, useEffect, useRef } from 'react'
import { m3Api, type HealthStatus } from '../api/m3'
import { useAuthStore } from '../stores/authStore'

export function useAuth() {
  const store = useAuthStore()
  const healthRef = useRef<HealthStatus | null>(null)

  useEffect(() => {
    m3Api.health()
      .then((h) => {
        healthRef.current = h
      })
      .catch(() => {
        healthRef.current = {
          status: 'ok',
          service: 'anvaya-api',
          environment: 'unknown',
          database: 'ok',
          public_demo_enabled: false,
        }
      })
  }, [])

  const login = useCallback(
    async (username: string, password: string) => {
      store.setBusy('login')
      store.clearError()
      try {
        const user = await m3Api.login(username, password)
        store.setUser(user)
        return user
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Login failed'
        store.setError(msg)
        return null
      } finally {
        store.setBusy('')
      }
    },
    [store],
  )

  const publicDemo = useCallback(async () => {
    store.setBusy('public-demo')
    store.clearError()
    try {
      const user = await m3Api.publicDemo()
      store.setUser(user)
      return user
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Demo login failed'
      store.setError(msg)
      return null
    } finally {
      store.setBusy('')
    }
  }, [store])

  const logout = useCallback(async () => {
    try {
      await m3Api.logout()
    } catch {
      // best-effort
    }
    store.setUser(null)
  }, [store])

  return {
    user: store.user,
    busy: store.busy,
    error: store.error,
    isSupervisor: store.user?.role === 'SUPERVISOR',
    health: healthRef.current,
    login,
    publicDemo,
    logout,
    clearError: store.clearError,
  }
}
