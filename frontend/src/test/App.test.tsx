import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'

import { App } from '../App'

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><App /></QueryClientProvider>)
}

function mockFoundationFetch(){
  vi.spyOn(globalThis,'fetch').mockImplementation(async input=>{
    const url=String(input)
    if(url.includes('/api/sources')) return new Response(JSON.stringify({request_id:'test',data:[],warnings:[]}),{status:200})
    return new Response(JSON.stringify({request_id:'test',data:{status:'ok',service:'anvaya-api',environment:'testing',database:'ok'},warnings:[]}),{status:200})
  })
}

describe('application shell', () => {
  it('renders the ANVAYA NEXUS shell', async () => {
    mockFoundationFetch()
    renderApp()
    expect(screen.getByRole('heading', { name: 'Explainable FIR Intelligence & Investigation Assurance' })).toBeInTheDocument()
    expect(screen.getByText(/Every generated statement and derived relationship/)).toBeInTheDocument()
    expect(await screen.findByText('ANVAYA NEXUS secure demo')).toBeInTheDocument()
  })

  it('keeps the synthetic prototype banner visible', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => undefined))
    renderApp()
    expect(screen.getByRole('note')).toHaveTextContent('SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE')
  })
})
