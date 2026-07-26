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
    expect(screen.getByRole('heading', { name: /Karnataka State Police/i })).toBeInTheDocument()
    expect(screen.getAllByText(/ANVAYA/i).length).toBeGreaterThanOrEqual(1)
  })

  it('shows the product name and feature cards', () => {
    renderApp()
    expect(screen.getAllByText(/ANVAYA/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/Karnataka State Police/i).length).toBeGreaterThanOrEqual(1)
  })
})
