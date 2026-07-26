import { QueryClient,QueryClientProvider } from '@tanstack/react-query'
import { fireEvent,render,screen,waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { DataReadinessPage } from '../features/data-readiness/DataReadinessPage'

const sources={request_id:'r',warnings:[],data:[{id:'CCTNS_REPLICA',name:'Synthetic CCTNS-style Case Replica',status:'Fresh',priority:'P0',version:'M2-1.0'},{id:'COURT_REPLICA',name:'Court Metadata Replica — P1',status:'Unavailable',priority:'P1',version:'M2-1.0'}]}
const job={id:'SYN-IMPORT-1',input_format:'json',mapped_fields:['external_id','fir_number'],missing_required_keys:[],accepted_count:2,failed_count:1,failures:[{row:3,category:'invalid_date',reason:'Invalid incident_at'}],status:'PARTIAL',import_timestamp:'2026-07-11T00:00:00Z',checksum:'abc123',source_version:'synthetic-import-1.0',committed_at:null}
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><DataReadinessPage/></QueryClientProvider>)}
function json(data:unknown,status=200){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}})}

it('renders file selection and source status badges',async()=>{vi.spyOn(globalThis,'fetch').mockResolvedValue(json(sources));renderPage();expect(screen.getByRole('heading',{name:'Data Readiness'})).toBeInTheDocument();expect(await screen.findByText(/Fresh/)).toBeInTheDocument();expect(screen.getByText(/Unavailable/)).toBeInTheDocument()})

it('tracks file selection',async()=>{vi.spyOn(globalThis,'fetch').mockResolvedValue(json(sources));renderPage();const file=new File(['[]'],'synthetic.json',{type:'application/json'});await userEvent.upload(screen.getByLabelText('Synthetic CSV or JSON file'),file);expect(screen.getByText('Selected: synthetic.json')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Validate'})).toBeEnabled()})

it('shows loading, success summaries and error table',async()=>{
  let release:(value:Response)=>void=()=>{};const pending=new Promise<Response>(resolve=>{release=resolve})
  vi.spyOn(globalThis,'fetch').mockImplementation(input=>String(input).includes('/api/sources')?Promise.resolve(json(sources)):pending)
  renderPage();await userEvent.upload(screen.getByLabelText('Synthetic CSV or JSON file'),new File(['[]'],'synthetic.json'));await userEvent.click(screen.getByRole('button',{name:'Validate'}));expect(screen.getByRole('button',{name:'Validating…'})).toBeDisabled();release(json({request_id:'r',warnings:[],data:job},201));expect(await screen.findByText('PARTIAL')).toBeInTheDocument();expect(screen.getByText('2')).toBeInTheDocument();expect(screen.getByText('invalid_date')).toBeInTheDocument();expect(screen.getByText('Invalid incident_at')).toBeInTheDocument()
})

it('shows validation failure',async()=>{vi.spyOn(globalThis,'fetch').mockImplementation(input=>String(input).includes('/api/sources')?Promise.resolve(json(sources)):Promise.resolve(json({code:'INVALID_IMPORT_FILE',message:'Invalid JSON'},400)));renderPage();await userEvent.upload(screen.getByLabelText('Synthetic CSV or JSON file'),new File(['bad'],'bad.json'));await userEvent.click(screen.getByRole('button',{name:'Validate'}));expect(await screen.findByRole('alert')).toHaveTextContent('Invalid JSON')})

it('shows commit success',async()=>{const committed={...job,status:'COMMITTED',committed_at:'2026-07-11T01:00:00Z'};vi.spyOn(globalThis,'fetch').mockImplementation(input=>{const url=String(input);if(url.includes('/api/sources'))return Promise.resolve(json(sources));if(url.includes('/commit'))return Promise.resolve(json({request_id:'r',warnings:[],data:committed}));return Promise.resolve(json({request_id:'r',warnings:[],data:job},201))});renderPage();await userEvent.upload(screen.getByLabelText('Synthetic CSV or JSON file'),new File(['[]'],'synthetic.json'));await userEvent.click(screen.getByRole('button',{name:'Validate'}));await screen.findByText('PARTIAL');await userEvent.click(screen.getByRole('button',{name:'Commit accepted rows'}));expect(await screen.findByRole('button',{name:'Accepted rows committed'})).toBeDisabled()})
