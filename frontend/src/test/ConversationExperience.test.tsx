import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {ConversationExperience} from '../features/m4/ConversationExperience'

const api=vi.hoisted(()=>({
 health:vi.fn(),publicDemo:vi.fn(),home:vi.fn(),sourceControl:vi.fn(),
 createInvestigation:vi.fn(),resolveChatAction:vi.fn(),briefing:vi.fn(),
 networkClusters:vi.fn(),conversationPdf:vi.fn(),case360:vi.fn(),logout:vi.fn(),
}))
vi.mock('../api/m3',()=>({m3Api:api}))

const investigation={id:'INV-1',title:'Conversation',purpose:'Active Case Investigation',selected_sources:['CCTNS_REPLICA'],assigned_station:'SYN-STN-01',assigned_district:'SYN-DIST-01'}
const briefing={headline:'Synthetic shift briefing',summary:{authorised_case_count:0,network_leads:0},sources:{degraded:[]},attention:[],quality_alerts:[],network_leads:[],mo_pattern_leads:[],limitations:['Synthetic prototype records only.']}

beforeEach(()=>{
 vi.clearAllMocks()
 localStorage.clear()
 api.health.mockResolvedValue({status:'ok',service:'anvaya-api',environment:'testing',database:'ok',public_demo_enabled:true})
 api.publicDemo.mockResolvedValue({id:'USER-1',username:'demo',role:'INVESTIGATOR',assigned_station:'SYN-STN-01',assigned_district:'SYN-DIST-01'})
 api.home.mockResolvedValue({})
 api.sourceControl.mockResolvedValue({sources:[]})
 api.createInvestigation.mockResolvedValue(investigation)
 api.resolveChatAction.mockRejectedValue(new Error('route unavailable'))
 api.briefing.mockResolvedValue(briefing)
})

async function openConversation(coach=false){
 if(!coach)localStorage.setItem('anvaya_coach_v1','dismissed')
 const user=userEvent.setup()
 render(<ConversationExperience/>)
 await user.click(await screen.findByRole('button',{name:'Open public demo'}))
 await screen.findByRole('heading',{name:/Chat with your case data/i})
 return user
}

it('shows empty-state help text',async()=>{
 await openConversation()
 expect(screen.getByText(/Need help\? Open the persistent Help button/i)).toBeInTheDocument()
})

it('dismisses and remembers the first-run coach',async()=>{
 const user=await openConversation(true)
 expect(screen.getByRole('dialog',{name:'ANVAYA first-run coach'})).toBeInTheDocument()
 await user.click(screen.getByRole('button',{name:'Skip'}))
 expect(screen.queryByRole('dialog',{name:'ANVAYA first-run coach'})).not.toBeInTheDocument()
 expect(localStorage.getItem('anvaya_coach_v1')).toBe('dismissed')
})

it('uses the local briefing regex when action resolution fails',async()=>{
 const user=await openConversation()
 await user.click(screen.getByRole('button',{name:'Show my shift briefing'}))
 expect(await screen.findByRole('region',{name:'Shift intelligence briefing'})).toBeInTheDocument()
 expect(api.briefing).toHaveBeenCalledWith('INV-1')
})

it('offers a retry control when an action fails',async()=>{
 api.briefing.mockRejectedValueOnce(new Error('Briefing temporarily unavailable'))
 const user=await openConversation()
 await user.click(screen.getByRole('button',{name:'Show my shift briefing'}))
 expect(await screen.findByRole('alert')).toHaveTextContent('Briefing temporarily unavailable')
 expect(screen.getByRole('button',{name:/Retry Preparing shift briefing/i})).toBeInTheDocument()
})

it('resolves and summarises candidate network clusters',async()=>{
 const user=await openConversation()
 api.resolveChatAction.mockResolvedValue({kind:'action',action:'NETWORK_CLUSTERS',case_ref:'SYN-CASE-0001'})
 api.networkClusters.mockResolvedValue({clusters:[{member_case_ids:['SYN-CASE-0001','SYN-CASE-0002']}]})
 await user.type(screen.getByLabelText('Ask ANVAYA'),'show network clusters for SYN-CASE-0001')
 await user.click(screen.getByRole('button',{name:/Send/}))
 expect(await screen.findByText(/SYN-CASE-0001, SYN-CASE-0002/)).toHaveTextContent(/human verification required/i)
 expect(api.networkClusters).toHaveBeenCalledWith('INV-1','SYN-CASE-0001')
})

it('exports redacted conversation turns',async()=>{
 const user=await openConversation()
 api.resolveChatAction.mockResolvedValue({kind:'action',action:'CONVERSATION_PDF',case_ref:null})
 api.conversationPdf.mockResolvedValue(undefined)
 await user.type(screen.getByLabelText('Ask ANVAYA'),'export chat')
 await user.click(screen.getByRole('button',{name:/Send/}))
 await waitFor(()=>expect(api.conversationPdf).toHaveBeenCalled())
 expect(api.conversationPdf).toHaveBeenCalledWith('INV-1',[expect.objectContaining({role:'user',text:'export chat',kind:'text',created_at:expect.any(String)})])
})

it('opens Case 360 with the investigation purpose',async()=>{
 api.case360.mockResolvedValue({case:{id:'SYN-CASE-0001',crime_number:'SYN-CRIME-00001'},overview:{id:'SYN-CASE-0001'},sections:[]})
 const user=await openConversation()
 api.resolveChatAction.mockResolvedValue({kind:'action',action:'OPEN_CASE_360',case_ref:'SYN-CASE-0001'})
 await user.type(screen.getByLabelText('Ask ANVAYA'),'open case SYN-CASE-0001')
 await user.click(screen.getByRole('button',{name:/Send/}))
 await waitFor(()=>expect(api.case360).toHaveBeenCalledWith('SYN-CASE-0001','Active Case Investigation',['CCTNS_REPLICA']))
})
