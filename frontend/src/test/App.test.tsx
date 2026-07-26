import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { App } from '../App'

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><App /></QueryClientProvider>)
}

describe('application shell', () => {
  it('renders the landing page', async () => {
    renderApp()
    expect(screen.getByRole('heading', { name: 'Ask. Discover. Verify. Report.' })).toBeInTheDocument()
    expect(screen.getByText(/no live KSP\/CCTNS connection/i)).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Start Exploring' }).length).toBeGreaterThanOrEqual(1)
  })

  it('shows the product name and feature cards', () => {
    renderApp()
    expect(screen.getByText('ANVAYA')).toBeInTheDocument()
    expect(screen.getByText('Search & Discover')).toBeInTheDocument()
    expect(screen.getByText('Investigate with AI Copilot')).toBeInTheDocument()
    expect(screen.getByText('Generate Cited Reports')).toBeInTheDocument()
  })
})
