import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'

import { HealthPage } from '../features/health/HealthPage'

function renderHealth() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><HealthPage /></QueryClientProvider>)
}

it('shows the loading state', () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => undefined))
  renderHealth()
  expect(screen.getByText('Checking local services…')).toBeInTheDocument()
})

it('shows the success state', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ request_id: 'health-1', data: { status: 'ok', service: 'anvaya-api', environment: 'development', database: 'ok' }, warnings: [] }), { status: 200 }))
  renderHealth()
  expect(await screen.findByText('All local foundation services are healthy')).toBeInTheDocument()
  expect(screen.getByText('anvaya-api')).toBeInTheDocument()
})

it('shows the failure state', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 503 }))
  renderHealth()
  expect(await screen.findByText('Health check failed')).toBeInTheDocument()
  expect(screen.getByText('The ANVAYA API is unavailable.')).toBeInTheDocument()
})
