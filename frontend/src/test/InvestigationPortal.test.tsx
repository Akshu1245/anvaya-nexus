import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {App} from '../App'
import {LocaleProvider} from '../i18n/portal'
import {InvestigationPortal} from '../features/portal/InvestigationPortal'

const api=vi.hoisted(()=>({
 health:vi.fn(),publicDemo:vi.fn(),home:vi.fn(),sourceControl:vi.fn(),
 createInvestigation:vi.fn(),preview:vi.fn(),followUp:vi.fn(),search:vi.fn(),discover:vi.fn(),
 case360:vi.fn(),briefing:vi.fn(),trends:vi.fn(),networkClusters:vi.fn(),
 brief:vi.fn(),briefPdf:vi.fn(),conversationPdf:vi.fn(),logout:vi.fn(),updateSources:vi.fn(),
 related:vi.fn(),firGraph:vi.fn(),priorities:vi.fn(),passport:vi.fn(),
}))
vi.mock('../api/m3',()=>({m3Api:api}))

const investigation={id:'INV-1',title:'Portal',purpose:'Active Case Investigation',selected_sources:['CCTNS_REPLICA'],assigned_station:'SYN-STN-01',assigned_district:'SYN-DIST-01'}
const userRow={id:'USER-1',username:'demo',role:'INVESTIGATOR',assigned_station:'SYN-STN-01',assigned_district:'SYN-DIST-01'}

beforeEach(()=>{
 vi.clearAllMocks()
 localStorage.clear()
 api.health.mockResolvedValue({status:'ok',service:'anvaya-api',environment:'testing',database:'ok',public_demo_enabled:true,voice_enabled:false})
 api.publicDemo.mockResolvedValue(userRow)
 api.home.mockResolvedValue({})
 api.sourceControl.mockResolvedValue({sources:[{id:'CCTNS_REPLICA',name:'CCTNS',selectable:true,status:'Fresh'}]})
 api.createInvestigation.mockResolvedValue(investigation)
 api.preview.mockResolvedValue({message_id:'MSG-1',normalised_interpretation:{intent:'SEARCH',filters:{offence:'ROBBERY',status:'UNRESOLVED'},selected_sources:['CCTNS_REPLICA'],result_limit:25}})
 api.followUp.mockResolvedValue({message_id:'MSG-2',parent_message_id:'MSG-1',normalised_interpretation:{intent:'SEARCH',filters:{offence:'ROBBERY',status:'UNRESOLVED',location:'Jayanagar'},selected_sources:['CCTNS_REPLICA'],result_limit:25},inherited_fields:['offence','status']})
 api.conversationPdf.mockResolvedValue(undefined)
 api.search.mockResolvedValue({results:[{case_id:'SYN-CASE-0001',crime_number:'SYN-CRIME-00001',status:'UNRESOLVED',offence:'CHAIN_SNATCHING'}]})
 api.case360.mockResolvedValue({case:{id:'SYN-CASE-0001',crime_number:'SYN-CRIME-00001'},overview:{id:'SYN-CASE-0001'},people:{witnesses:[{person_id:'W1',display_name:'Witness A',role:'WITNESS'}],complainants:[],victims:[],accused:[]},statements:[{id:'S1',display_name:'Witness A',statement_text:'Saw the incident.'}],police_and_court:{unit_name:'Unit 1',investigating_officer:{display_name:'IO Demo'}},sections:[{id:'people',label:'People'}],assurance:{summary:{},findings:[]}})
 api.briefing.mockResolvedValue({headline:'Briefing',summary:{authorised_case_count:1},attention:[],quality_alerts:[],network_leads:[],mo_pattern_leads:[],limitations:[],sources:{degraded:[]}})
 api.trends.mockResolvedValue({summary:{authorised_case_count:3,earliest_month:'2026-01',latest_month:'2026-07'},monthly_incidents:[{month:'2026-07',count:2}],station_hotspots:[],offence_distribution:[],seasonal_month_of_year:[{month_of_year:7,label:'July',count:2}],mo_cooccurrence:[{left:'NIGHT',right:'TWO_WHEELER',count:1}],methodology:{method:'descriptive',limitations:[]}})
})

function renderPortal(section:'search'|'briefing'|'trends'|'chat'='search'){
 const onSectionChange=vi.fn()
 const view=render(<LocaleProvider><InvestigationPortal section={section} onSectionChange={onSectionChange}/></LocaleProvider>)
 return {user:userEvent.setup(),onSectionChange,...view}
}

async function enterDemo(user:ReturnType<typeof userEvent.setup>){
 await user.click(await screen.findByRole('button',{name:'Open public demo'},{timeout:5000}))
 await screen.findByRole('heading',{name:/Investigation Portal|ತನಿಖಾ ಪೋರ್ಟಲ್/i})
}

it('shows the FIR filter form on the search section',async()=>{
 const {user}=renderPortal('search')
 await enterDemo(user)
 expect(screen.getAllByText(/FIR filters|FIR ಫಿಲ್ಟರ್/i).length).toBeGreaterThan(0)
 expect(screen.getByLabelText(/Offence/i)).toBeInTheDocument()
})

it('opens Case 360 with purpose and sources',async()=>{
 const {user}=renderPortal('search')
 await enterDemo(user)
 await user.type(screen.getByLabelText(/Offence/i),'Chain snatching')
 await user.type(screen.getByLabelText(/^Status$/i),'UNRESOLVED')
 await user.click(screen.getByRole('button',{name:/Search records|ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ/i}))
 expect(await screen.findByText(/SYN-CRIME-00001/)).toBeInTheDocument()
 await user.click(screen.getByRole('button',{name:/Open Case 360|Case 360 ತೆರೆಯಿರಿ/i}))
 await waitFor(()=>expect(api.case360).toHaveBeenCalledWith('SYN-CASE-0001','Active Case Investigation',['CCTNS_REPLICA']))
 expect(await screen.findByRole('dialog')).toBeInTheDocument()
 expect(screen.getAllByText(/Witness A/).length).toBeGreaterThan(0)
})

it('loads trends with seasonality fields',async()=>{
 const {user}=renderPortal('trends')
 await enterDemo(user)
 await user.click(screen.getByRole('button',{name:/Load crime trends|ಪ್ರವೃತ್ತಿಗಳನ್ನು ಲೋಡ್/i}))
 expect(await screen.findByText(/Seasonality/i)).toBeInTheDocument()
 expect(screen.getByText(/Modus operandi co-occurrence/i)).toBeInTheDocument()
})

it('exports the mounted chat conversation as a PDF',async()=>{
 const {user}=renderPortal('chat')
 await enterDemo(user)
 await user.type(screen.getByLabelText('Ask ANVAYA'),'Find unresolved robbery cases')
 await user.click(screen.getByRole('button',{name:'Send'}))
 await user.click(screen.getByRole('button',{name:'Save conversation PDF'}))
 await waitFor(()=>expect(api.conversationPdf).toHaveBeenCalledWith('INV-1',expect.arrayContaining([
  expect.objectContaining({role:'user',text:'Find unresolved robbery cases',kind:'text'}),
 ])))
})

it('keeps prior query context for a mounted chat follow-up',async()=>{
 const {user}=renderPortal('chat')
 await enterDemo(user)
 await user.type(screen.getByLabelText('Ask ANVAYA'),'Find unresolved robbery cases')
 await user.click(screen.getByRole('button',{name:'Send'}))
 expect(await screen.findByText(/prepared an editable interpretation/i)).toBeInTheDocument()
 await user.type(screen.getByLabelText('Ask ANVAYA'),'Only near Jayanagar')
 await user.click(screen.getByRole('button',{name:'Send'}))
 await waitFor(()=>expect(api.followUp).toHaveBeenCalledWith('INV-1','MSG-1','Only near Jayanagar'))
 expect(await screen.findByText(/Kept offence, status/)).toBeInTheDocument()
})

it('switches chrome language via locale provider in App',async()=>{
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}})
 api.health.mockResolvedValue({status:'ok',service:'anvaya-api',environment:'testing',database:'ok',public_demo_enabled:true})
 render(<QueryClientProvider client={client}><App/></QueryClientProvider>)
 const user=userEvent.setup()
 await user.click(screen.getByRole('button',{name:'ಕನ್ನಡ',pressed:false}))
 expect(screen.getByRole('button',{name:'ಕನ್ನಡ',pressed:true})).toBeInTheDocument()
 expect(screen.getByRole('navigation',{name:/Portal navigation/i})).toHaveTextContent(/ಹುಡುಕಾಟ|Search/)
})
