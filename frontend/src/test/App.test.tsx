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
    return new Response(JSON.stringify({request_id:'test',data:{status:'ok',service:'anvaya-api',environment:'testing',database:'ok',public_demo_enabled:true},warnings:[]}),{status:200})
  })
}

describe('application shell', () => {
  it('renders the Challenge 01 application shell', async () => {
    mockFoundationFetch()
    renderApp()
    expect(screen.getByRole('heading', { name: 'Ask. Discover. Verify. Brief.' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Open ANVAYA demo' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Open public demo' })).toBeInTheDocument()
    expect(screen.getByText(/no live KSP\/CCTNS connection/i)).toBeInTheDocument()
  })

  it('keeps the synthetic prototype banner visible', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => undefined))
    renderApp()
    expect(screen.getByRole('note')).toHaveTextContent('SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE')
  })
})
