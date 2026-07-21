import {useEffect,useRef,useState,type ReactNode} from 'react'
import {m3Api,type HealthStatus,type Investigation,type Source,type User} from '../../api/m3'
import {OFFENCE_CATALOGUE,OffenceBadge,OffenceVisual} from '../../components/OffenceVisual'
import {JourneyStepper,type JourneyStage} from '../../components/ui'
import {SourcePassportDrawer} from './SourcePassportDrawer'
import {
 LoginLanding,
 QueryInterpretationPanel,
 CrimeTrendsPanel,
 Case360Workspace,
 RelatedCasesPanel,
 FirRelationshipGraph,
 ShiftBriefingPanel,
 CaseComparePanel,
 VerificationPriorityPanel,
 BriefPreviewPanel,
 RecordAssurancePanel,
} from './InvestigationExperience'

const LANGUAGES=[
 {code:'en-IN',label:'English',sarvamCode:'en-IN'},
 {code:'kn-IN',label:'ಕನ್ನಡ',sarvamCode:'kn-IN'},
 {code:'hi-IN',label:'हिन्दी',sarvamCode:'hi-IN'},
]

const examples=[
 'Find unresolved chain snatching at SYN-STN-01',
 'ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ ಜಯನಗರ ತೋರಿಸಿ',
 'Show my shift briefing',
 'Show recorded crime trends',
 'Last three months alli Jayanagar hatra similar unresolved chain-snatching cases show maadi.',
]

function isBriefingAsk(text:string){
 const t=text.toLowerCase()
 return /\b(shift\s*briefing|daily\s*briefing|my\s*briefing)\b/.test(t)||t.includes('ಬ್ರೀಫಿಂಗ್')
}
function isTrendsAsk(text:string){
 const t=text.toLowerCase()
 return /\b(crime\s*trends?|aggregate\s*trends?|recorded\s*crime)\b/.test(t)||t.includes('ಪ್ರವೃತ್ತಿ')
}

const CASE_TOKEN=/\b(SYN-CASE-\d{4}|SYN-FIR-[A-Z0-9-]+|SYN-CRIME-[A-Z0-9-]+)\b/i
function localChatAction(text:string,context:{active_case_id?:string|null}){
 const raw=text.trim()
 const caseRef=raw.match(CASE_TOKEN)?.[1]?.toUpperCase()||context.active_case_id||null
 if(isBriefingAsk(raw))return {kind:'action',action:'BRIEFING',case_ref:caseRef}
 if(isTrendsAsk(raw))return {kind:'action',action:'TRENDS',case_ref:caseRef}
 if(/conversation\s*pdf|chat\s*(history|transcript)\s*pdf|export\s*(this\s*)?chat|save\s*conversation/i.test(raw))return {kind:'action',action:'CONVERSATION_PDF',case_ref:caseRef}
 if(/send\s*(me\s*)?(pdf|dossier)|download\s*(pdf|dossier)|export\s*(pdf|dossier)|dossier\s*pdf/i.test(raw))return caseRef?{kind:'action',action:'DOWNLOAD_PDF',case_ref:caseRef}:{kind:'action',action:'NEED_CASE_FOR_PDF',case_ref:null,message:'Open a case first, or include a synthetic case id such as SYN-CASE-0001.'}
 if(/complete\s*details?|full\s*(case|details?|fir)|case\s*360|open\s*case|fir\s*details?/i.test(raw))return caseRef?{kind:'action',action:'OPEN_CASE_360',case_ref:caseRef}:{kind:'action',action:'NEED_CASE_FOR_DETAILS',case_ref:null,message:'Tell me which synthetic case to open, or open a search result first.'}
 if(/network\s*cluster|candidate\s*cluster|connected\s*cases/i.test(raw))return caseRef?{kind:'action',action:'NETWORK_CLUSTERS',case_ref:caseRef}:{kind:'action',action:'NEED_CASE_FOR_CLUSTER',case_ref:null,message:'Provide a synthetic case id to inspect candidate clusters.'}
 return {kind:'query',action:null,case_ref:caseRef}
}

const BUSY_LABELS:Record<string,string>={
 login:'Signing in…','public-demo':'Opening demo…',ask:'Interpreting question…',briefing:'Preparing shift briefing…',
 trends:'Loading recorded trends…',search:'Searching synthetic records…',answer:'Composing source-backed answer…',
 case:'Opening Case 360…',related:'Finding factual connections…',graph:'Building relationship view…',
 priorities:'Preparing review priorities…',assurance:'Checking record assurance…',brief:'Preparing case dossier…',
 'brief-pdf':'Generating case dossier PDF…','conversation-pdf':'Exporting conversation PDF…',passport:'Checking source details…',
 'network-clusters':'Checking candidate factual clusters…',
}

const coachSteps=[
 {title:'Ask in the composer',text:'Use English, ಕನ್ನಡ, हिन्दी or code-mixed phrases in the composer.'},
 {title:'Try an example',text:'Example chips show useful synthetic searches and shortcuts.'},
 {title:'Confirm before search',text:'ANVAYA never runs an interpreted record search until you click Search records.'},
 {title:'Open Case 360',text:'Inspect a result in-thread and check its source passports.'},
 {title:'Export a dossier',text:'Ask “send me PDF” after opening a case, or export the chat from Help.'},
]

const emptyFilters={crime_number:'',case_number:'',case_identifier:'',registration_date_from:'',registration_date_to:'',date_from:'',date_to:'',person_name:'',person_role:'',act_code:'',section_code:'',case_category:'',gravity_offence:'',crime_major_head:'',crime_minor_head:'',canonical_case_status:'',arrest_event_type:'',chargesheet_report_type:'',state:'',district:'',police_unit:'',registering_officer:'',court:''}
const caseIdOf=(detail:any)=>detail?.case?.id||detail?.overview?.id
const titleCase=(value:string)=>value.replaceAll('_',' ').toLowerCase()

function describeInterpretation(preview:any){
 const plan=preview?.normalised_interpretation||{}
 const filters=plan.filters||{}
 const subject=filters.offence?`for ${titleCase(String(filters.offence))} `:''
 const scope:string[]=[]
 if(filters.location)scope.push(`near ${filters.location}`)
 if(filters.status)scope.push(String(filters.status).toLowerCase())
 if(filters.date_from||filters.date_to)scope.push(`between ${filters.date_from||'the start'} and ${filters.date_to||'now'}`)
 const action=plan.intent==='DISCOVER'?'look for related and similar FIRs':'search FIR records'
 const scopeText=scope.length?scope.join(', '):'across the selected sources'
 const confidence=Math.round((plan.confidence||0)*100)
 const sources=(plan.selected_sources||[]).join(', ')||'the selected sources'
 const engineBadge=preview.interpretation_engine==='ai_assisted'?'AI-assisted':'deterministic'
 return {text:`I read this as: ${action} ${subject}${scopeText}. Confidence ${confidence}%. Confirm or edit below and I will query ${sources}.`,engine:engineBadge}
}

const chipsFor=(preview:any)=>{
 const filters=preview?.normalised_interpretation?.filters||{}
 return Object.entries(filters).filter(([,value])=>value).map(([key,value])=>`${titleCase(key)}: ${value}`)
}

function EngineBadge({engine}:{engine:string}){
 const isAI=engine==='ai_assisted'||engine==='ai-assisted'
 return <span className={`animate-scale-in rounded-full px-2 py-0.5 text-[10px] font-semibold ${isAI?'bg-purple-100 text-purple-800 ring-1 ring-purple-200':'bg-slate-100 text-slate-600 ring-1 ring-slate-200'}`}>{isAI?'✦ AI-assisted':'Deterministic'}</span>
}

function Assistant({children}:{children:ReactNode}){
 return <div className="flex animate-fade-in-up gap-3">
  <div className="mt-1 hidden h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-navy-900 to-teal-800 text-center text-xs font-bold leading-8 text-teal-300 shadow-sm ring-1 ring-teal-500/30 sm:block">AN</div>
  <div className="min-w-0 flex-1 space-y-3">{children}</div>
 </div>
}

function Bubble({children}:{children:ReactNode}){
 return <div className="inline-block max-w-full rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-bubble">{children}</div>
}

export function ConversationExperience(){
 const [user,setUser]=useState<User|null>(null)
 const [password,setPassword]=useState('')
 const [username,setUsername]=useState('investigator.demo')
 const [home,setHome]=useState<any>(null)
 const [control,setControl]=useState<any>(null)
 const [inv,setInv]=useState<Investigation|null>(null)
 const [selected,setSelected]=useState<string[]>(['CCTNS_REPLICA'])
 const [language,setLanguage]=useState(LANGUAGES[0])
 const [input,setInput]=useState('')
 const [messages,setMessages]=useState<any[]>([])
 const [parentMessageId,setParentMessageId]=useState('')
 const [passport,setPassport]=useState<any>(null)
 const [filters,setFilters]=useState({...emptyFilters})
 const [hasArrest,setHasArrest]=useState(false)
 const [hasChargesheet,setHasChargesheet]=useState(false)
 const [showSources,setShowSources]=useState(false)
 const [recording,setRecording]=useState(false)
 const [busy,setBusy]=useState('')
 const [error,setError]=useState('')
 const [health,setHealth]=useState<HealthStatus|null>(null)
 const [activeCaseId,setActiveCaseId]=useState<string|null>(null)
 const [stage,setStage]=useState<JourneyStage>('ASK')
 const [maxStage,setMaxStage]=useState<JourneyStage>('ASK')
 const [helpOpen,setHelpOpen]=useState(false)
 const [coachStep,setCoachStep]=useState(()=>localStorage.getItem('anvaya_coach_v1')? -1:0)
 const [lastFailedAction,setLastFailedAction]=useState<{label:string;run:()=>void}|null>(null)
 const bottomRef=useRef<HTMLDivElement|null>(null)
 const mediaRecorderRef=useRef<MediaRecorder|null>(null)
 const audioChunksRef=useRef<Blob[]>([])
 const speechCtor=typeof window!=='undefined'?((window as any).SpeechRecognition||(window as any).webkitSpeechRecognition):null

 useEffect(()=>{void m3Api.health().then(setHealth).catch(()=>setHealth({status:'ok',service:'anvaya-api',environment:'unknown',database:'ok',public_demo_enabled:false,ai_assist_enabled:false,voice_enabled:false}))},[])
 useEffect(()=>{if(typeof bottomRef.current?.scrollIntoView==='function')bottomRef.current.scrollIntoView({behavior:'smooth',block:'end'})},[messages,busy])

 const uid=()=>Math.random().toString(36).slice(2)
 const say=(message:any)=>setMessages(list=>[...list,{id:uid(),...message}])
 const update=(id:string,patch:any)=>setMessages(list=>list.map(item=>item.id===id?{...item,...patch}:item))
 const advance=(next:JourneyStage)=>{const order:JourneyStage[]=['ASK','DISCOVER','VERIFY','PRIORITISE','REPORT'];setStage(next);setMaxStage(current=>order.indexOf(next)>order.indexOf(current)?next:current)}
 const call=async(label:string,fn:()=>Promise<any>,retry?:()=>void)=>{
  setBusy(label);setError('')
  try{const value=await fn();setLastFailedAction(null);return value}
  catch(e){setError((e as Error).message);setLastFailedAction({label,run:retry||(()=>{void call(label,fn)})});return null}
  finally{setBusy('')}
 }
 const load=async()=>{const [nextHome,nextControl]=await Promise.all([m3Api.home(),m3Api.sourceControl('Active Case Investigation')]);setHome(nextHome);setControl(nextControl)}

 async function login(){const next=await call('login',()=>m3Api.login(username,password));if(next){setUser(next);await load()}}
 async function publicDemo(){const next=await call('public-demo',()=>m3Api.publicDemo());if(next){setUser(next);await load()}}
 function resetConversation(){setMessages([]);setInv(null);setParentMessageId('');setInput('');setActiveCaseId(null);setStage('ASK');setMaxStage('ASK')}

 function dismissCoach(){
  localStorage.setItem('anvaya_coach_v1','dismissed')
  setCoachStep(-1)
 }

 function startGuidedDemo(){
  setHelpOpen(false)
  setInput('Find unresolved chain snatching at SYN-STN-01')
  say({role:'assistant',kind:'text',text:'Guided demo: send the prepared synthetic query. I will show my interpretation first.'})
  say({role:'assistant',kind:'text',text:'Next, review the filters and click “Search records” yourself. The demo will not confirm a search for you.'})
  say({role:'assistant',kind:'text',text:'After results appear, open Case 360, check sources, then ask “send me PDF”.'})
 }

 function defaultPurpose(role?:User['role']){
  if(role==='CRIME_ANALYST')return 'Pattern Research'
  if(role==='SUPERVISOR')return 'Supervisor Review'
  return 'Active Case Investigation'
 }

 async function ensureInvestigation(){
  if(inv)return inv
  const created=await m3Api.createInvestigation({title:'Conversational investigation',purpose:defaultPurpose(user?.role),selected_sources:selected.length?selected:['CCTNS_REPLICA']})
  setInv(created);setSelected(created.selected_sources);return created
 }

 const redactTurns=(sourceMessages:any[])=>sourceMessages.map(message=>({
  role:message.role,
  text:message.text||message.kind||'',
  kind:message.kind||'text',
  created_at:new Date().toISOString(),
 }))

 async function exportConversationPdf(sourceMessages=messages){
  const done=await call('conversation-pdf',async()=>{
   const investigation=await ensureInvestigation()
   await m3Api.conversationPdf(investigation.id,redactTurns(sourceMessages))
   return true
  },()=>void exportConversationPdf(sourceMessages))
  if(done)say({role:'assistant',kind:'text',text:'Conversation PDF export started.'})
 }

 async function ask(raw?:string){
  const text=(raw??input).trim();if(!text||busy)return
  setInput('');say({role:'user',text})
  const investigation=await call('ask',()=>ensureInvestigation(),()=>void ask(text))
  if(!investigation){say({role:'assistant',kind:'text',text:'I could not open an investigation. Check the connection and try again.'});return}
  const context={active_case_id:activeCaseId}
  const resolved=await m3Api.resolveChatAction(investigation.id,text,context).catch(()=>localChatAction(text,context))
  if(resolved?.kind==='action'){
   const caseRef=resolved.case_ref||activeCaseId
   if(resolved.action==='BRIEFING'){
    const data=await call('briefing',()=>m3Api.briefing(investigation.id),()=>void ask(text))
    if(data){say({role:'assistant',kind:'briefing',data});advance('DISCOVER')}
   }else if(resolved.action==='TRENDS'){
    const data=await call('trends',()=>m3Api.trends(investigation.id),()=>void ask(text))
    if(data){say({role:'assistant',kind:'trends',data});advance('DISCOVER')}
   }else if(resolved.action==='OPEN_CASE_360'&&caseRef){
    await openCase(caseRef)
   }else if(resolved.action==='DOWNLOAD_PDF'&&caseRef){
    setActiveCaseId(caseRef);advance('REPORT')
    const done=await call('brief-pdf',()=>m3Api.briefPdf(investigation.id,caseRef),()=>void ask(text))
    if(done!==null)say({role:'assistant',kind:'text',text:`Case dossier download started for ${caseRef}. Verify all cited synthetic records before use.`})
   }else if(resolved.action==='CONVERSATION_PDF'){
    await exportConversationPdf([...messages,{role:'user',text}])
   }else if(resolved.action==='NETWORK_CLUSTERS'&&caseRef){
    setActiveCaseId(caseRef)
    const data=await call('network-clusters',()=>m3Api.networkClusters(investigation.id,caseRef),()=>void ask(text))
    if(data){
     const clusters=data.clusters||[]
     const summary=clusters.length
      ?clusters.map((cluster:any)=>`${(cluster.member_case_ids||[]).join(', ')} — Candidate factual connection based on authorised stored relationship records only; human verification required.`).join('\n')
      :'No candidate factual clusters were found for this case in the authorised synthetic records.'
     say({role:'assistant',kind:'text',text:summary})
     advance('VERIFY')
    }
   }else if(String(resolved.action).startsWith('NEED_CASE_')){
    say({role:'assistant',kind:'text',text:resolved.message||'Open a synthetic case result first, or include its case id.'})
   }else{
    say({role:'assistant',kind:'text',text:'That guided action is not available in this prototype.'})
   }
   return
  }
  const value=await call('ask',()=>parentMessageId?m3Api.followUp(investigation.id,parentMessageId,text):m3Api.preview(investigation.id,text),()=>void ask(text))
  if(!value){say({role:'assistant',kind:'text',text:'I could not interpret that question. Try naming an offence, a place, a status, or a date range — or ask for "shift briefing" / "crime trends".'});return}
  const conversation=await m3Api.history(investigation.id).catch(()=>[] as any[])
  setParentMessageId(conversation.at(-1)?.id||'')
  say({role:'assistant',kind:'interpretation',preview:value})
 }

 async function runSearch(messageId:string,preview:any){
  const investigation=inv;if(!investigation)return
  const base=preview.normalised_interpretation
  const plan={...base,filters:{...base.filters,...Object.fromEntries(Object.entries(filters).filter(([,value])=>value)),...(hasArrest?{has_arrest_event:true}:{}),...(hasChargesheet?{has_chargesheet:true}:{})}}
  update(messageId,{confirmed:true})
  const data=await call('search',()=>plan.intent==='DISCOVER'?m3Api.discover(investigation.id,plan):m3Api.search(investigation.id,plan))
  if(!data)return
  const results=data.results||[]
  if(results.length===0){
   say({role:'assistant',kind:'text',text:'No authorised synthetic records matched those filters. Edit the interpretation, broaden the date or location, or try another example.'})
   return
  }
  setActiveCaseId(results[0].case_id||results[0].id||null)
  advance('DISCOVER')
  say({role:'assistant',kind:'results',results,plan})
  if(investigation&&results.length>0){
   const question=[...messages].reverse().find(m=>m.role==='user'&&m.text)?.text||''
   const answerData=await call('answer',()=>m3Api.aiAnswer(investigation.id,{plan,question,results}))
   if(answerData)say({role:'assistant',kind:'answer',answer:answerData,plan,results})
  }
 }

 async function openCase(id:string){
  const investigation=await call('case',()=>ensureInvestigation(),()=>void openCase(id))
  if(!investigation)return
  const detail=await call('case',()=>m3Api.case360(id,investigation.purpose),()=>void openCase(id))
  if(detail){const caseId=caseIdOf(detail)||id;setActiveCaseId(caseId);advance('VERIFY');say({role:'assistant',kind:'case',detail,caseId})}
 }
 async function showRelated(id:string){if(!inv)return;const data=await call('related',()=>m3Api.related(inv.id,id),()=>void showRelated(id));if(data){setActiveCaseId(id);advance('VERIFY');say({role:'assistant',kind:'related',data,baseId:id})}}
 async function showGraph(id:string){if(!inv)return;const data=await call('graph',()=>m3Api.firGraph(inv.id,id));if(data)say({role:'assistant',kind:'graph',data,baseId:id,path:null})}
 async function showPriorities(id:string){if(!inv)return;const data=await call('priorities',()=>m3Api.priorities(inv.id,id),()=>void showPriorities(id));if(data){advance('PRIORITISE');say({role:'assistant',kind:'priorities',data})}}
 async function showAssurance(id:string){if(!inv)return;const data=await call('assurance',()=>m3Api.firAssurance(inv.id,id));if(data)say({role:'assistant',kind:'assurance',data,caseId:id})}
 async function showBrief(id:string){if(!inv)return;const data=await call('brief',()=>m3Api.brief(inv.id,id),()=>void showBrief(id));if(data){advance('REPORT');say({role:'assistant',kind:'brief',data,caseId:id})}}
 async function compareCases(baseId:string,rightId:string){if(!inv)return;const data=await call('compare',()=>m3Api.compare(inv.id,baseId,rightId));if(data)say({role:'assistant',kind:'compare',data})}
 async function showPath(messageId:string,baseId:string,targetId:string){if(!inv)return;const data=await call('path',()=>m3Api.firGraphPath(inv.id,baseId,targetId));if(data)update(messageId,{path:data})}
 async function resolveAssurance(messageId:string,caseId:string,findingId:string,status:string){if(!inv)return;await call('assurance',()=>m3Api.updateFirAssurance(inv.id,caseId,findingId,{status}));const data=await m3Api.firAssurance(inv.id,caseId).catch(()=>null);if(data)update(messageId,{data})}
 async function toggleSource(id:string,on:boolean){const next=on?[...selected,id]:selected.filter(item=>item!==id);setSelected(next);if(inv){const updated=await call('sources',()=>m3Api.updateSources(inv.id,next));if(updated)setInv(updated)}}
 const openPassport=(id:string)=>void call('passport',async()=>{const investigation=await ensureInvestigation();return m3Api.passport(id,investigation.purpose)}).then(value=>value&&setPassport(value))

 async function speakText(text:string){
  const data=await call('speak',()=>m3Api.voiceSpeak(text,language.sarvamCode))
  if(!data?.audio_base64)return
  try{const bytes=atob(data.audio_base64);const buffer=new Uint8Array(bytes.length);for(let i=0;i<bytes.length;i++)buffer[i]=bytes.charCodeAt(i);const blob=new Blob([buffer],{type:'audio/wav'});const url=URL.createObjectURL(blob);const audio=new Audio(url);audio.play();audio.onended=()=>URL.revokeObjectURL(url)}catch{/* ignore audio errors */}}

 async function startSarvamRecording(){
  if(recording){mediaRecorderRef.current?.stop();return}
  try{
   const stream=await navigator.mediaDevices.getUserMedia({audio:true})
   const mimeType=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm'
   const recorder=new MediaRecorder(stream,{mimeType})
   audioChunksRef.current=[];setRecording(true)
   recorder.ondataavailable=e=>{if(e.data.size>0)audioChunksRef.current.push(e.data)}
   recorder.onstop=async()=>{
    setRecording(false);stream.getTracks().forEach(t=>t.stop())
    const audioBlob=new Blob(audioChunksRef.current,{type:mimeType})
    const result=await call('transcribe',()=>m3Api.voiceTranscribe(audioBlob,language.sarvamCode)).catch(()=>null)
    if(result?.text)setInput(current=>current?`${current} ${result.text}`:result.text)
    else setError('Could not transcribe audio. Try typing your question instead.')
   }
   mediaRecorderRef.current=recorder;recorder.start()
  }catch{setError('Microphone access was denied or unavailable. Type your question instead.')}
 }

 function startBrowserSpeech(){
  if(!speechCtor)return
  const recognition=new speechCtor()
  recognition.lang=language.code;recognition.interimResults=false
  recognition.onresult=(event:any)=>{const transcript=event.results?.[0]?.[0]?.transcript||'';setInput(current=>current?`${current} ${transcript}`:transcript)}
  recognition.onerror=()=>setError('Voice input was unavailable. Type your question instead.')
  recognition.start()
 }

 function handleMic(){
  if(health?.voice_enabled)void startSarvamRecording()
  else startBrowserSpeech()
 }

 function renderMessage(message:any){
  if(message.role==='user')return <div key={message.id} className="flex animate-slide-in-right justify-end"><div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-gradient-to-br from-teal-600 to-teal-800 px-4 py-2.5 text-sm text-white shadow-bubble">{message.text}</div></div>

  if(message.kind==='text')return <Assistant key={message.id}><Bubble>{message.text}</Bubble></Assistant>

  if(message.kind==='interpretation'){
   const {text,engine}=describeInterpretation(message.preview)
   const chips=chipsFor(message.preview)
   const setPreview=(preview:any)=>update(message.id,{preview})
   const quickStatus=()=>setPreview({...message.preview,normalised_interpretation:{...message.preview.normalised_interpretation,filters:{...message.preview.normalised_interpretation.filters,status:'UNRESOLVED'}}})
   const quickDates=()=>{const to=new Date(),from=new Date(Date.now()-90*86400000);setPreview({...message.preview,normalised_interpretation:{...message.preview.normalised_interpretation,filters:{...message.preview.normalised_interpretation.filters,date_from:from.toISOString().slice(0,10),date_to:to.toISOString().slice(0,10)}}})}
   return <Assistant key={message.id}>
    <Bubble>
     <div className="flex flex-wrap items-start gap-2"><p className="flex-1">{text}</p><EngineBadge engine={engine}/></div>
     {chips.length>0&&<div className="mt-2 flex flex-wrap gap-1.5">{chips.map(chip=><span key={chip} className="rounded-full bg-teal-50 px-2 py-0.5 text-xs text-teal-900">{chip}</span>)}</div>}
    </Bubble>
    <details className="rounded-xl border border-slate-200 bg-slate-50 p-3">
     <summary className="cursor-pointer text-xs font-semibold text-slate-600">Show / edit how I read this</summary>
     <div className="mt-3 space-y-3">
      <div className="flex flex-wrap gap-2"><button className="rounded-full border px-3 py-1 text-xs" onClick={quickStatus}>Unresolved only</button><button className="rounded-full border px-3 py-1 text-xs" onClick={quickDates}>Last 90 days</button></div>
      <QueryInterpretationPanel preview={message.preview} onChange={setPreview}/>
      <details><summary className="cursor-pointer text-xs font-medium">Advanced FIR filters</summary>
       <div className="mt-2 grid gap-2 sm:grid-cols-2">{Object.keys(filters).map(key=><label key={key} className="text-xs">{titleCase(key)}<input className="ml-2 rounded border p-1" value={filters[key as keyof typeof filters]} onChange={event=>setFilters({...filters,[key]:event.target.value})}/></label>)}<label className="text-xs"><input type="checkbox" checked={hasArrest} onChange={event=>setHasArrest(event.target.checked)}/> Has arrest/surrender</label><label className="text-xs"><input type="checkbox" checked={hasChargesheet} onChange={event=>setHasChargesheet(event.target.checked)}/> Has chargesheet</label></div>
      </details>
     </div>
    </details>
    {message.confirmed?<p className="animate-fade-in text-xs font-semibold text-teal-700">Searched ✓</p>:<button data-coach="confirm" className="rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 hover:shadow-glow disabled:opacity-60 disabled:shadow-none" disabled={Boolean(busy)} onClick={()=>void runSearch(message.id,message.preview)}>{busy==='search'?'Searching…':'Search records'}</button>}
   </Assistant>
  }

  if(message.kind==='answer'){
   const ai=message.answer
   return <Assistant key={message.id}>
    <div className={`animate-scale-in rounded-2xl rounded-tl-sm border px-4 py-3 text-sm leading-relaxed shadow-bubble ${ai.engine==='ai_assisted'?'border-purple-200 bg-gradient-to-br from-purple-50 to-white':'border-slate-200 bg-white'}`}>
     <div className="flex flex-wrap items-start gap-2"><p className="flex-1 text-slate-800">{ai.answer}</p><EngineBadge engine={ai.engine}/></div>
     {ai.cited_source_ids?.length>0&&<div className="mt-3"><p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">Check sources</p><div className="flex flex-wrap gap-1.5">{ai.cited_source_ids.map((id:string)=><button type="button" key={id} onClick={()=>openPassport(id)} className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] text-slate-600 ring-1 ring-slate-200 transition-colors hover:bg-teal-50 hover:text-teal-800">{id}</button>)}</div></div>}
     {health?.voice_enabled&&<button className="mt-2 rounded-full border border-slate-300 px-2 py-1 text-xs hover:border-teal-500 hover:bg-teal-50 hover:text-teal-800 disabled:opacity-50" disabled={Boolean(busy)} onClick={()=>void speakText(ai.answer)}>🔊 Listen</button>}
     <p className="mt-1 text-[10px] text-slate-400">{ai.grounded?'Source-backed · human review required':''}</p>
    </div>
   </Assistant>
  }

  if(message.kind==='results')return <Assistant key={message.id}>
   <div className="grid gap-2 sm:grid-cols-2">{message.results.map((item:any,index:number)=><article key={item.case_id||item.id} style={{animationDelay:`${Math.min(index*60,360)}ms`}} className="animate-fade-in-up overflow-hidden rounded-xl border border-slate-200 bg-white shadow-bubble transition-all hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-panel">
    <OffenceVisual offence={item.offence||item.category?.name||item.crime_major_head?.name}/>
    <div className="p-4">
     <div className="flex items-start justify-between gap-2"><b className="text-sm">{item.crime_number||item.fir_number||item.case_id}</b>{item.masking?.applied&&<span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-900">Masked</span>}</div>
     <div className="mt-1.5 flex flex-wrap items-center gap-1.5"><OffenceBadge offence={item.offence||item.category?.name||item.crime_major_head?.name}/><span className="text-xs text-slate-600">{item.canonical_status?.name||item.status||'Status unavailable'}</span></div>
     <p className="mt-1 text-xs text-slate-500">{item.police_unit?.name||item.station_id||'Unit unavailable'} · Registered {item.registered_at||'—'}</p>
     <button data-coach="case-360" className="mt-3 rounded-lg border border-teal-700 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-700 hover:text-white disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void openCase(item.case_id||item.id)}>Open Case 360</button>
    </div>
   </article>)}</div>
  </Assistant>

  if(message.kind==='case')return <Assistant key={message.id}>
   <Case360Workspace detail={message.detail} onPassport={openPassport}/>
   <div className="flex flex-wrap gap-2">
    <button className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void showRelated(message.caseId)}>Related cases</button>
    <button className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void showGraph(message.caseId)}>Relationship graph</button>
    <button className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void showPriorities(message.caseId)}>Verification priorities</button>
    <button className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void showAssurance(message.caseId)}>Record assurance</button>
    <button className="rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void showBrief(message.caseId)}>Grounded brief</button>
   </div>
  </Assistant>

  if(message.kind==='related')return <Assistant key={message.id}><RelatedCasesPanel data={message.data} onOpen={id=>void openCase(id)} onCompare={id=>void compareCases(message.baseId,id)}/></Assistant>
  if(message.kind==='graph')return <Assistant key={message.id}><FirRelationshipGraph data={message.data} path={message.path} onOpen={id=>void openCase(id)} onPath={targetId=>void showPath(message.id,message.baseId,targetId)}/></Assistant>
  if(message.kind==='priorities')return <Assistant key={message.id}><VerificationPriorityPanel data={message.data}/></Assistant>
  if(message.kind==='compare')return <Assistant key={message.id}><CaseComparePanel data={message.data}/></Assistant>
  if(message.kind==='briefing')return <Assistant key={message.id}><ShiftBriefingPanel data={message.data}/></Assistant>
  if(message.kind==='trends')return <Assistant key={message.id}><CrimeTrendsPanel data={message.data}/></Assistant>
  if(message.kind==='brief')return <div data-coach="pdf" key={message.id}><Assistant><BriefPreviewPanel data={message.data} busy={busy==='brief-pdf'} onDownload={()=>void call('brief-pdf',()=>m3Api.briefPdf(inv!.id,message.caseId),()=>void call('brief-pdf',()=>m3Api.briefPdf(inv!.id,message.caseId)))}/></Assistant></div>
  if(message.kind==='assurance')return <Assistant key={message.id}><RecordAssurancePanel data={message.data} canResolve={user?.role==='SUPERVISOR'} onUpdate={(findingId,status)=>void resolveAssurance(message.id,message.caseId,findingId,status)}/></Assistant>
  return null
 }

 if(!user)return <LoginLanding username={username} password={password} busy={busy} error={error} health={health} onSelect={setUsername} onPassword={setPassword} onLogin={()=>void login()} onPublicDemo={()=>void publicDemo()}/>

 const voiceAvailable=Boolean(health?.voice_enabled)||Boolean(speechCtor)

 return <section aria-label="Conversational investigation" className="flex min-h-[70vh] flex-col gap-4">
  <header className="animate-fade-in rounded-2xl bg-gradient-to-br from-navy-950 via-navy-900 to-teal-900 p-5 text-white shadow-panel">
   <div className="flex flex-wrap items-center justify-between gap-3">
    <div><p className="text-xs uppercase tracking-[0.2em] text-teal-300">{user.role}</p><h2 className="text-xl font-semibold">ANVAYA · Chat with your case data</h2><p className="text-xs text-teal-100/80">{user.assigned_station||'Pattern scope'} · {user.assigned_district||'—'}</p></div>
    <div className="flex flex-wrap items-center gap-2">
     <div className="flex rounded-lg border border-white/20 bg-white/10 p-0.5" role="group" aria-label="Language">
      {LANGUAGES.map(lang=><button key={lang.code} onClick={()=>setLanguage(lang)} className={`rounded-md px-2 py-1 text-xs font-semibold transition-colors ${language.code===lang.code?'bg-teal-600 text-white':'text-white/70 hover:text-white'}`}>{lang.label}</button>)}
     </div>
     <button className="rounded-lg border border-white/30 px-3 py-1.5 text-xs disabled:opacity-60" disabled={Boolean(busy)} onClick={resetConversation}>New chat</button>
     <button className="rounded-lg border border-white/30 px-3 py-1.5 text-xs disabled:opacity-60" disabled={Boolean(busy)} onClick={()=>void m3Api.logout().then(()=>{setUser(null);resetConversation()})}>Logout</button>
    </div>
   </div>
   <div className="mt-3 flex flex-wrap items-center gap-2">
    {health?.ai_assist_enabled&&<span className="animate-scale-in rounded-full bg-purple-500/20 px-3 py-0.5 text-xs font-semibold text-purple-200 ring-1 ring-purple-400/40">✦ AI Assist ON</span>}
    {health?.voice_enabled&&<span className="animate-scale-in rounded-full bg-teal-500/20 px-3 py-0.5 text-xs font-semibold text-teal-200 ring-1 ring-teal-400/40">🎙 Sarvam Voice ON</span>}
   </div>
   <details className="mt-3 rounded-lg bg-white/5 p-3" open={showSources} onToggle={event=>setShowSources((event.target as HTMLDetailsElement).open)}>
    <summary className="cursor-pointer text-xs font-semibold text-teal-200">Sources · {selected.length} selected</summary>
    <div className="mt-2 flex flex-wrap gap-2">{control?.sources?.filter((source:Source)=>source.selectable).map((source:Source)=><label key={source.id} className="rounded border border-white/20 px-2 py-1 text-xs"><input type="checkbox" checked={selected.includes(source.id)} onChange={event=>void toggleSource(source.id,event.target.checked)}/> {source.name}</label>)}</div>
   </details>
   {home?.degraded_mode&&<p className="mt-3 rounded bg-amber-200 p-2 text-xs text-amber-950">Degraded sources: {home.degraded_sources?.join(', ')}. Authorised available records remain accessible.</p>}
  </header>

  <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-bubble">
   <JourneyStepper current={stage} maxReached={maxStage} onSelect={setStage}/>
  </div>

  <div className="flex-1 space-y-4">
   {messages.length===0&&<div className="animate-fade-in-up rounded-2xl border border-slate-200 bg-white p-6 shadow-bubble">
    <div className="flex items-center gap-3">
     <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-navy-900 text-lg text-white shadow-sm">💬</div>
     <div><h3 className="text-lg font-semibold">Ask everything here</h3><p className="text-xs text-slate-500">English · ಕನ್ನಡ · हिन्दी · code-mixed · one chat only</p></div>
    </div>
    <p className="mt-3 text-sm text-slate-600">There are no separate menus for search, briefing, trends, Case 360 or briefs. Type or speak what you need in this chat — ANVAYA answers only from authorised synthetic records, with confirmation and source citations.</p>
    <p className="mt-2 text-xs text-slate-500">Need help? Open the persistent Help button for supported phrases or start the guided demo.</p>
    {health?.ai_assist_enabled&&<p className="mt-2 rounded-lg bg-purple-50 p-2 text-xs text-purple-800 ring-1 ring-purple-100">✦ AI Assist is active — questions may be interpreted by AI, while answers remain bounded to synthetic prototype records. The human-confirmation gate remains in place.</p>}
    <div className="mt-4 grid gap-2 sm:grid-cols-4">
     {OFFENCE_CATALOGUE.map((item,index)=><button key={item.code} type="button" style={{animationDelay:`${index*70}ms`}} className="animate-fade-in-up overflow-hidden rounded-xl border border-slate-200 bg-white text-left shadow-bubble transition-all hover:-translate-y-0.5 hover:border-teal-400 hover:shadow-panel" onClick={()=>void ask(`Find unresolved ${item.label.toLowerCase()} cases`)}>
      <img src={item.src} alt="" className="aspect-[4/3] w-full object-contain" loading="lazy"/>
      <span className="block border-t border-slate-100 bg-white px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-navy-950">{item.label}</span>
     </button>)}
    </div>
    <div data-coach="examples" className="mt-4 flex flex-wrap gap-2">{examples.map((example,index)=><button key={example} style={{animationDelay:`${index*80}ms`}} className="animate-fade-in-up rounded-full border border-slate-300 px-3 py-1.5 text-xs transition-all hover:-translate-y-0.5 hover:border-teal-500 hover:bg-teal-50 hover:text-teal-900 hover:shadow-sm" onClick={()=>void ask(example)}>{example}</button>)}</div>
    <div className="mt-5 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-4">
     {[
      {step:'1',title:'Ask in chat',text:'Type or speak — search, briefing, trends, everything starts here.'},
      {step:'2',title:'Confirm',text:'Review how ANVAYA read it — edit filters before anything runs.'},
      {step:'3',title:'Inspect in thread',text:'Case 360, related cases and graphs open as chat replies.'},
      {step:'4',title:'Brief',text:'Ask for a grounded brief — download cited PDF from the reply.'},
     ].map((item,index)=><div key={item.step} style={{animationDelay:`${index*90}ms`}} className="animate-fade-in-up rounded-xl bg-slate-50 p-3 ring-1 ring-slate-100">
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-teal-600 to-teal-800 text-[11px] font-bold text-white">{item.step}</span>
      <p className="mt-2 text-xs font-bold text-navy-950">{item.title}</p>
      <p className="mt-0.5 text-[11px] leading-4 text-slate-500">{item.text}</p>
     </div>)}
    </div>
    <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xl border border-teal-100 bg-teal-50/50 px-3 py-2 text-[11px] text-teal-900">
     <span className="font-bold uppercase tracking-wide">Safeguards active</span>
     <span>🛡 Server-side policy</span><span>🎭 Jurisdiction masking</span><span>📜 Full audit trail</span><span>✅ Human confirmation</span><span>🔗 Source citations</span>
    </div>
   </div>}
   {messages.map(renderMessage)}
   {busy&&<Assistant><Bubble><span className="inline-flex items-center gap-1.5 text-slate-500"><span className="h-2 w-2 animate-bounce rounded-full bg-teal-500"/><span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:150ms]"/><span className="h-2 w-2 animate-bounce rounded-full bg-teal-500 [animation-delay:300ms]"/><span className="ml-1">{BUSY_LABELS[busy]||'Working…'}</span></span></Bubble></Assistant>}
   <div ref={bottomRef}/>
  </div>

  <form data-coach="composer" className="sticky bottom-0 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur" onSubmit={event=>{event.preventDefault();void ask()}}>
   <div className="flex items-end gap-2">
    <textarea aria-label="Ask ANVAYA" rows={1} className="max-h-40 min-h-11 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2.5 text-sm focus:border-teal-500 focus:shadow-glow" placeholder={`Ask in ${language.label} or code-mixed — e.g. unresolved chain snatching near Jayanagar`} value={input} onChange={event=>setInput(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();void ask()}}}/>
    <button type="button" aria-label={recording?'Stop recording':'Start voice input'} className={`h-11 rounded-xl border px-3 text-sm disabled:opacity-50 ${recording?'animate-pulse-ring border-red-400 bg-red-50 text-red-600':'border-slate-300 hover:border-teal-500 hover:bg-teal-50'}`} disabled={!voiceAvailable||Boolean(busy)} onClick={handleMic}>{recording?'⏹':'🎙'}</button>
    <button type="submit" className="h-11 rounded-xl bg-gradient-to-br from-teal-600 to-teal-800 px-4 text-sm font-semibold text-white shadow-sm hover:from-teal-500 hover:to-teal-700 hover:shadow-glow disabled:opacity-60 disabled:shadow-none" disabled={Boolean(busy)||!input.trim()}>{busy?(BUSY_LABELS[busy]||'Working…'):'Send ➤'}</button>
   </div>
   {!voiceAvailable&&<p className="mt-1 text-[11px] text-slate-400">Voice recognition is unavailable in this browser; typing works everywhere.</p>}
   {recording&&<p className="mt-1 text-[11px] text-red-500">Recording… tap ⏹ to stop and transcribe.</p>}
   {parentMessageId&&<button type="button" className="mt-1 text-[11px] text-teal-700 underline" onClick={()=>setParentMessageId('')}>Start a new topic (clear follow-up context)</button>}
   <p className="mt-2 rounded-lg bg-blue-50 px-2 py-1.5 text-[11px] leading-4 text-blue-900">Prototype only · not monitored · synthetic data only · cannot file an FIR or contact emergency services. Call 112 for emergencies.</p>
  </form>

  {passport&&<SourcePassportDrawer passport={passport} onClose={()=>setPassport(null)}/>}
  {error&&<div role="alert" className="animate-fade-in-up flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 shadow-sm"><span>{error}</span>{lastFailedAction&&<button type="button" onClick={()=>{setError('');lastFailedAction.run()}} className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-bold hover:bg-red-100">Retry {BUSY_LABELS[lastFailedAction.label]?.replace('…','')||'action'}</button>}</div>}

  <button type="button" aria-expanded={helpOpen} onClick={()=>setHelpOpen(value=>!value)} className="fixed bottom-5 right-5 z-30 rounded-full bg-blue-700 px-5 py-3 text-sm font-bold text-white shadow-lg ring-4 ring-blue-200 hover:bg-blue-800">Help</button>
  {helpOpen&&<aside aria-label="ANVAYA help" className="fixed bottom-20 right-5 z-30 w-[min(22rem,calc(100vw-2.5rem))] rounded-2xl border border-blue-200 bg-white p-5 shadow-2xl">
   <div className="flex items-center justify-between"><h3 className="font-semibold text-navy-950">Try these phrases</h3><button type="button" aria-label="Close help" onClick={()=>setHelpOpen(false)}>✕</button></div>
   <ul className="mt-3 space-y-2 text-sm text-slate-700">
    {['shift briefing','crime trends','complete details','send me PDF','export chat','golden query: unresolved chain snatching near Jayanagar'].map(phrase=><li key={phrase}><button type="button" className="w-full rounded-lg bg-slate-50 px-3 py-2 text-left hover:bg-blue-50" onClick={()=>{setInput(phrase.replace('golden query: ',''));setHelpOpen(false)}}>{phrase}</button></li>)}
   </ul>
   <button type="button" onClick={startGuidedDemo} className="mt-4 w-full rounded-lg bg-blue-700 px-3 py-2 text-sm font-bold text-white hover:bg-blue-800">Start guided demo</button>
   <button type="button" disabled={Boolean(busy)} onClick={()=>{setHelpOpen(false);void exportConversationPdf()}} className="mt-2 w-full rounded-lg border border-blue-300 bg-white px-3 py-2 text-sm font-bold text-blue-800 hover:bg-blue-50 disabled:opacity-60">Export conversation PDF</button>
  </aside>}

  {coachStep>=0&&<div className="fixed inset-0 z-40 flex items-center justify-center bg-blue-950/55 p-5">
   <section role="dialog" aria-modal="true" aria-label="ANVAYA first-run coach" className="relative w-full max-w-md rounded-2xl border-2 border-blue-300 bg-white p-6 shadow-2xl ring-8 ring-blue-400/30">
    <span className="text-xs font-bold uppercase tracking-widest text-blue-700">Step {coachStep+1} of {coachSteps.length}</span>
    <h3 className="mt-2 text-xl font-semibold text-navy-950">{coachSteps[coachStep].title}</h3>
    <p className="mt-2 text-sm leading-6 text-slate-600">{coachSteps[coachStep].text}</p>
    <div className="mt-5 flex items-center justify-between">
     <button type="button" onClick={dismissCoach} className="text-sm font-semibold text-slate-500 hover:text-slate-800">Skip</button>
     <button type="button" onClick={()=>coachStep===coachSteps.length-1?dismissCoach():setCoachStep(step=>step+1)} className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-bold text-white hover:bg-blue-800">{coachStep===coachSteps.length-1?'Finish':'Next'}</button>
    </div>
   </section>
  </div>}
 </section>
}
