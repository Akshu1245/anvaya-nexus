import {useEffect,useMemo,useRef,useState} from 'react'
import {m3Api,type HealthStatus,type Investigation,type Source,type User} from '../../api/m3'
import {btnOutline,btnPrimary,btnSecondary} from '../../components/PortalButtons'
import {PortalModal} from '../../components/PortalModal'
import {JourneyStepper,type JourneyStage,type PortalSection} from '../../components/ui'
import {useLocale} from '../../i18n/portal'
import {OffenceBadge,OFFENCE_CATALOGUE} from '../../components/OffenceVisual'
import {
 BriefPreviewPanel,
 Case360Workspace,
 CrimeTrendsPanel,
 FirRelationshipGraph,
 LoginLanding,
 NetworkClustersPanel,
 QueryInterpretationPanel,
 RecordAssurancePanel,
 RelatedCasesPanel,
 ShiftBriefingPanel,
 VerificationPriorityPanel,
} from '../m4/InvestigationExperience'
import {SourcePassportDrawer} from '../m4/SourcePassportDrawer'

const emptyFilters={
 crime_number:'',case_number:'',case_identifier:'',registration_date_from:'',registration_date_to:'',
 date_from:'',date_to:'',person_name:'',person_role:'',act_code:'',section_code:'',
 case_category:'',gravity_offence:'',crime_major_head:'',crime_minor_head:'',canonical_case_status:'',
 arrest_event_type:'',chargesheet_report_type:'',state:'',district:'',police_unit:'',registering_officer:'',court:'',
 offence:'',location:'',status:'',
}

const stageOrder:JourneyStage[]=['ASK','DISCOVER','VERIFY','PRIORITISE','REPORT']
const caseIdOf=(detail:any)=>detail?.case?.id||detail?.overview?.id

function defaultPurpose(role?:User['role']){
 if(role==='CRIME_ANALYST')return 'Pattern Research'
 if(role==='SUPERVISOR')return 'Supervisor Review'
 return 'Active Case Investigation'
}

const VOICE_BY_LOCALE={en:{label:'English',code:'en-IN',sarvamCode:'en-IN'},kn:{label:'ಕನ್ನಡ',code:'kn-IN',sarvamCode:'kn-IN'},hi:{label:'हिन्दी',code:'hi-IN',sarvamCode:'hi-IN'}} as const

type Props={section:PortalSection;onSectionChange:(s:PortalSection)=>void}

export function InvestigationPortal({section,onSectionChange}:Props){
 const {locale,t}=useLocale()
 const [user,setUser]=useState<User|null>(null)
 const [password,setPassword]=useState('')
 const [username,setUsername]=useState('investigator.demo')
 const [health,setHealth]=useState<HealthStatus|null>(null)
 const [control,setControl]=useState<any>(null)
 const [inv,setInv]=useState<Investigation|null>(null)
 const [selected,setSelected]=useState<string[]>(['CCTNS_REPLICA'])
 const [query,setQuery]=useState('')
 const [preview,setPreview]=useState<any>(null)
 const [filters,setFilters]=useState({...emptyFilters})
 const [hasArrest,setHasArrest]=useState(false)
 const [hasChargesheet,setHasChargesheet]=useState(false)
 const [results,setResults]=useState<any[]>([])
 const [searched,setSearched]=useState(false)
 const [detail,setDetail]=useState<any>(null)
 const [caseOpen,setCaseOpen]=useState(false)
 const [passport,setPassport]=useState<any>(null)
 const [briefing,setBriefing]=useState<any>(null)
 const [trends,setTrends]=useState<any>(null)
 const [related,setRelated]=useState<any>(null)
 const [graph,setGraph]=useState<any>(null)
 const [clusters,setClusters]=useState<any>(null)
 const [priorities,setPriorities]=useState<any>(null)
 const [brief,setBrief]=useState<any>(null)
 const [briefOpen,setBriefOpen]=useState(false)
 const [stage,setStage]=useState<JourneyStage>('ASK')
 const [maxStage,setMaxStage]=useState<JourneyStage>('ASK')
 const [busy,setBusy]=useState('')
 const [error,setError]=useState('')
 const [chatInput,setChatInput]=useState('')
 const [chatLog,setChatLog]=useState<Array<{id:string;role:string;text:string}>>([])
 const [pendingTranscript,setPendingTranscript]=useState('')
 const [recording,setRecording]=useState(false)
 const mediaRecorderRef=useRef<MediaRecorder|null>(null)
 const audioChunksRef=useRef<Blob[]>([])
 const speechCtor=typeof window!=='undefined'?((window as any).SpeechRecognition||(window as any).webkitSpeechRecognition):null
 const isSupervisor=user?.role==='SUPERVISOR'
 const voiceLang=VOICE_BY_LOCALE[locale==='kn'?'kn':'en']

 useEffect(()=>{void m3Api.health().then(setHealth).catch(()=>setHealth({status:'ok',service:'anvaya-api',environment:'unknown',database:'ok',public_demo_enabled:false}))},[])

 const advance=(next:JourneyStage)=>{setStage(next);setMaxStage(current=>stageOrder.indexOf(next)>stageOrder.indexOf(current)?next:current)}
 const call=async(label:string,fn:()=>Promise<any>)=>{setBusy(label);setError('');try{return await fn()}catch(e){setError((e as Error).message);return null}finally{setBusy('')}}

 const load=async()=>{
  const purpose=defaultPurpose(user?.role)
  const [homeIgnored,nextControl]=await Promise.all([m3Api.home().catch(()=>null),m3Api.sourceControl(isSupervisor?'Supervisor Review':purpose).catch(()=>({sources:[]}))])
  void homeIgnored
  setControl(nextControl)
 }

 async function login(){const next=await call('login',()=>m3Api.login(username,password));if(next){setUser(next)}}
 async function publicDemo(){const next=await call('public-demo',()=>m3Api.publicDemo());if(next){setUser(next)}}
 useEffect(()=>{if(user)void load()},[user?.id,user?.role])

 async function ensureInvestigation(){
  if(inv)return inv
  if(isSupervisor)throw new Error(locale==='kn'?'ಮೇಲ್ವಿಚಾರಕರು ವಿಮರ್ಶೆ-ಮಾತ್ರ. ಹುಡುಕಾಟ/ಬ್ರೀಫಿಂಗ್ ಲಭ್ಯವಿಲ್ಲ.':'Supervisor Review is review-only in this prototype. Search and briefing are not available.')
  const created=await m3Api.createInvestigation({title:'Portal investigation',purpose:defaultPurpose(user?.role),selected_sources:selected.length?selected:['CCTNS_REPLICA']})
  setInv(created);setSelected(created.selected_sources);return created
 }

 async function doPreview(){
  const text=query.trim();if(!text){setError(locale==='kn'?'ಪ್ರಶ್ನೆ ನಮೂದಿಸಿ ಅಥವಾ ಕೆಳಗಿನ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಬಳಸಿ.':'Enter a question or fill the filters below.');return}
  const investigation=await call('preview',()=>ensureInvestigation())
  if(!investigation)return
  const value=await call('preview',()=>m3Api.preview(investigation.id,text))
  if(value){setPreview(value);advance('ASK');onSectionChange('search')}
 }

 async function runSearch(){
  if(isSupervisor){setError('Supervisor Review does not grant investigation search powers.');return}
  const investigation=await call('search',()=>ensureInvestigation())
  if(!investigation)return
  const base=preview?.normalised_interpretation||{
   intent:'SEARCH',confidence:0.5,uncertain_fields:[],selected_sources:selected,
   result_limit:25,filters:{},
  }
  const mergedFilters={
   ...base.filters,
   ...Object.fromEntries(Object.entries(filters).filter(([,v])=>v)),
   ...(hasArrest?{has_arrest_event:true}:{}),
   ...(hasChargesheet?{has_chargesheet:true}:{}),
  }
  const meaningful=Object.values(mergedFilters).some(v=>v!==null&&v!==undefined&&v!==''&&v!==false)
  if(!meaningful&&!preview){setError(locale==='kn'?'ಕನಿಷ್ಠ ಒಂದು ಫಿಲ್ಟರ್ ಹೊಂದಿಸಿ (ಉದಾ. ಅಪರಾಧ, ಸ್ಥಳ, ಸ್ಥಿತಿ) ನಂತರ ಹುಡುಕಿ.':'Set at least one filter (offence, place, or status), then search.');onSectionChange('search');return}
  const plan={...base,filters:mergedFilters,selected_sources:selected.length?selected:base.selected_sources}
  const data=await call('search',()=>plan.intent==='DISCOVER'?m3Api.discover(investigation.id,plan):m3Api.search(investigation.id,plan))
  if(!data)return
  setResults(data.results||[])
  setSearched(true)
  advance('DISCOVER')
  onSectionChange('search')
 }

 async function openCase(caseId:string){
  const investigation=inv||await call('case',()=>ensureInvestigation())
  if(!investigation&&!isSupervisor)return
  const purpose=(investigation||inv)?.purpose||defaultPurpose(user?.role)
  const sources=(investigation||inv)?.selected_sources||selected
  const data=await call('case',()=>m3Api.case360(caseId,purpose,sources))
  if(data){setDetail(data);setCaseOpen(true);setRelated(null);setGraph(null);setClusters(null);setPriorities(null);advance('VERIFY')}
 }

 async function loadBriefing(){
  if(isSupervisor){setError('Supervisor Review does not grant briefing access.');return}
  const investigation=await call('briefing',()=>ensureInvestigation());if(!investigation)return
  const data=await call('briefing',()=>m3Api.briefing(investigation.id))
  if(data){setBriefing(data);onSectionChange('briefing');advance('PRIORITISE')}
 }

 async function loadTrends(){
  if(isSupervisor){setError('Supervisor Review does not grant trends access.');return}
  const investigation=await call('trends',()=>ensureInvestigation());if(!investigation)return
  const data=await call('trends',()=>m3Api.trends(investigation.id))
  if(data){setTrends(data);onSectionChange('trends');advance('PRIORITISE')}
 }

 async function showRelated(caseId:string){if(!inv)return;const data=await call('related',()=>m3Api.related(inv.id,caseId));if(data){setRelated(data);advance('PRIORITISE')}}
 async function showGraph(caseId:string){if(!inv)return;const data=await call('graph',()=>m3Api.firGraph(inv.id,caseId));if(data){setGraph(data);advance('PRIORITISE')}}
 async function showClusters(caseId:string){if(!inv)return;const data=await call('clusters',()=>m3Api.networkClusters(inv.id,caseId));if(data){setClusters(data);advance('PRIORITISE')}}
 async function showPriorities(caseId:string){if(!inv)return;const data=await call('priorities',()=>m3Api.priorities(inv.id,caseId));if(data){setPriorities(data);advance('PRIORITISE')}}
 async function prepareBrief(caseId:string){if(!inv)return;const data=await call('brief',()=>m3Api.brief(inv.id,caseId));if(data){setBrief(data);setBriefOpen(true);advance('REPORT')}}
 async function downloadBriefPdf(){if(!inv||!detail)return;const id=caseIdOf(detail);await call('brief-pdf',()=>m3Api.briefPdf(inv.id,id))}

 const openPassport=(id:string)=>void call('passport',()=>m3Api.passport(id,inv?.purpose||defaultPurpose(user?.role))).then(v=>v&&setPassport(v))

 function onJourney(next:JourneyStage){
  setStage(next)
  if(next==='ASK'||next==='DISCOVER')onSectionChange('search')
  if(next==='VERIFY'&&detail)setCaseOpen(true)
  if(next==='PRIORITISE'){if(briefing)onSectionChange('briefing');else if(trends)onSectionChange('trends')}
  if(next==='REPORT'&&brief)setBriefOpen(true)
 }

 const chatHelpPhrases=useMemo(()=>[
  locale==='kn'?'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ತೋರಿಸಿ':'Show my shift briefing',
  locale==='kn'?'ಅಪರಾಧ ಪ್ರವೃತ್ತಿಗಳು':'Show crime trends',
  'Find unresolved chain snatching at SYN-STN-01',
  'Open case SYN-CASE-0001',
  'send me PDF',
 ],[locale])

 async function maybeTranslateOutgoing(text:string){
  if(locale!=='kn'||!health?.voice_enabled)return text
  try{
   const translated=await m3Api.voiceTranslate(text,'kn-IN','en-IN')
   return translated?.text||text
  }catch{return text}
 }

 async function runChat(raw?:string){
  const typed=(raw??chatInput).trim();if(!typed||busy)return
  setChatInput('')
  setChatLog(list=>[...list,{id:Math.random().toString(36).slice(2),role:'user',text:typed}])
  const forEngine=await maybeTranslateOutgoing(typed)
  const lower=forEngine.toLowerCase()
  if(/briefing|ಬ್ರೀಫಿಂಗ್/i.test(lower)||/shift/i.test(lower)){await loadBriefing();setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:locale==='kn'?'ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್ ವಿಭಾಗ ತೆರೆಯಲಾಗಿದೆ.':'Opened the Shift Briefing section.'}]);return}
  if(/trend|ಪ್ರವೃತ್ತಿ/i.test(lower)){await loadTrends();setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:locale==='kn'?'ಪ್ರವೃತ್ತಿ ವಿಭಾಗ ತೆರೆಯಲಾಗಿದೆ.':'Opened the Crime Trends section.'}]);return}
  const caseMatch=forEngine.match(/SYN-CASE-\d+/i)
  if(/open\s*case|case\s*360|complete\s*details/i.test(lower)&&caseMatch){await openCase(caseMatch[0].toUpperCase());setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:`Opened Case 360 for ${caseMatch[0].toUpperCase()}.`}]);return}
  if(/pdf|dossier/i.test(lower)){
   const id=caseIdOf(detail)||caseMatch?.[0]?.toUpperCase()
   if(!id){setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:locale==='kn'?'ಮೊದಲು Case 360 ತೆರೆಯಿರಿ.':'Open a Case 360 first, then ask for the PDF.'}]);return}
   await prepareBrief(id)
   setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:locale==='kn'?'ಡಾಸಿಯರ್ ಪೂರ್ವವೀಕ್ಷಣೆ ತೆರೆಯಲಾಗಿದೆ — ಡೌನ್‌ಲೋಡ್ ಮಾಡುವ ಮೊದಲು ಪರಿಶೀಲಿಸಿ.':'Dossier preview opened — review before download.'}])
   return
  }
  if(/network|cluster/i.test(lower)){
   const id=caseIdOf(detail)||caseMatch?.[0]?.toUpperCase()
   if(!id){setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:'Open a case first for network clusters.'}]);return}
   await showClusters(id)
   setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:'Network clusters loaded in the Case 360 drawer.'}])
   return
  }
  setQuery(forEngine)
  onSectionChange('search')
  setChatLog(l=>[...l,{id:Math.random().toString(36).slice(2),role:'assistant',text:locale==='kn'?'ಪ್ರಶ್ನೆಯನ್ನು ಹುಡುಕಾಟ ವಿಭಾಗಕ್ಕೆ ಕಳುಹಿಸಲಾಗಿದೆ. “ಪ್ರಶ್ನೆ ಪೂರ್ವವೀಕ್ಷಣೆ” ನಂತರ “ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ” ಕ್ಲಿಕ್ ಮಾಡಿ.':'Sent your question to Search. Click Preview, review filters, then Search records.'}])
 }

 async function startVoice(){
  if(health?.voice_enabled){
   if(recording){mediaRecorderRef.current?.stop();return}
   try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true})
    const recorder=new MediaRecorder(stream);mediaRecorderRef.current=recorder;audioChunksRef.current=[]
    recorder.ondataavailable=e=>{if(e.data.size)audioChunksRef.current.push(e.data)}
    recorder.onstop=async()=>{
     setRecording(false);stream.getTracks().forEach(t=>t.stop())
     const blob=new Blob(audioChunksRef.current,{type:'audio/webm'})
     const data=await call('voice',()=>m3Api.voiceTranscribe(blob,voiceLang.sarvamCode))
     if(data?.text)setPendingTranscript(data.text)
    }
    recorder.start();setRecording(true)
   }catch{setError('Microphone unavailable.')}
   return
  }
  if(!speechCtor){setError('Voice input unavailable in this browser.');return}
  const recognition=new speechCtor();recognition.lang=voiceLang.code;recognition.interimResults=false
  recognition.onresult=(event:any)=>{const transcript=event.results?.[0]?.[0]?.transcript||'';setPendingTranscript(transcript)}
  recognition.onerror=()=>setError('Voice input failed. Type instead.')
  recognition.start()
 }

 if(!user){
  return <LoginLanding username={username} password={password} busy={busy} error={error} health={health} onSelect={setUsername} onPassword={setPassword} onLogin={()=>void login()} onPublicDemo={()=>void publicDemo()}/>
 }

 const workspaceSection=section==='briefing'||section==='trends'||section==='chat'?section:'search'
 const queryInvalid=Boolean(error)&&!query.trim()&&!Object.values(filters).some(Boolean)&&!hasArrest&&!hasChargesheet

 return <div className="grid gap-5">
  <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border bg-white p-4 shadow-sm">
   <div>
    <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">{user.role} · {user.assigned_station||'—'} · {user.assigned_district||'—'}</p>
    <h2 className="text-xl font-bold text-navy-950">{locale==='kn'?'ತನಿಖಾ ಪೋರ್ಟಲ್':'Investigation Portal'}</h2>
    {locale==='kn'&&!health?.voice_enabled&&<p className="mt-1 text-xs text-amber-800">{t('languageNoticeKn')}</p>}
   </div>
   <button type="button" className={btnOutline} disabled={Boolean(busy)} onClick={()=>void m3Api.logout().then(()=>{setUser(null);setInv(null);setResults([]);setDetail(null)})}>{locale==='kn'?'ಲಾಗ್ ಔಟ್':'Logout'}</button>
  </div>

  <JourneyStepper current={stage} maxReached={maxStage} onSelect={onJourney}/>

  {error&&<div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"><span>{error}</span><button type="button" className={btnOutline} onClick={()=>setError('')}>{t('close')}</button></div>}
  {busy&&<p role="status" className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700">{t('loading')} — {busy}</p>}

  {isSupervisor&&<aside className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">Supervisor Review is review-only in this prototype. Search, briefing and trends stay closed to match policy.</aside>}

  {workspaceSection==='search'&&!isSupervisor&&<section className="grid gap-5" aria-label="Search workspace">
   <div className="rounded-2xl border bg-white p-5 shadow-sm">
    <h3 className="text-lg font-semibold text-navy-950">{t('searchTitle')}</h3>
    <p className="mt-1 text-sm text-slate-600">{t('searchLead')}</p>
    <label className="mt-4 block text-sm font-medium">{locale==='kn'?'ಪ್ರಶ್ನೆ (ಐಚ್ಛಿಕ)':'Question (optional)'}
     <textarea aria-label="Investigation question" aria-invalid={queryInvalid||undefined} className={`mt-1 min-h-20 w-full rounded-xl border p-3 transition focus:ring-2 focus:ring-teal-300 ${queryInvalid?'border-red-300 bg-red-50/40':'border-slate-200'}`} value={query} onChange={e=>setQuery(e.target.value)} placeholder={locale==='kn'?'ಉದಾ. ಬಗೆಹರಿಯದ ಸರಗಳ್ಳತನ SYN-STN-01':'e.g. unresolved chain snatching near SYN-STN-01'}/>
     {queryInvalid&&<span className="mt-1 flex items-center gap-1 text-xs font-normal text-red-700"><span aria-hidden>⚠</span>{locale==='kn'?'ಪ್ರಶ್ನೆ ನಮೂದಿಸಿ ಅಥವಾ ಕೆಳಗಿನ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಬಳಸಿ.':'Enter a question or set a filter below.'}</span>}
    </label>
    <div className="mt-3 flex flex-wrap gap-2">
     <button type="button" className={btnSecondary} disabled={Boolean(busy)} onClick={()=>void doPreview()}>{busy==='preview'?t('loading'):t('previewQuery')}</button>
     <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={()=>void runSearch()}>{busy==='search'?t('loading'):t('searchRecords')}</button>
     <button type="button" className={btnOutline} onClick={()=>{setFilters({...emptyFilters});setHasArrest(false);setHasChargesheet(false);setPreview(null)}}>{t('clear')}</button>
    </div>
    <div className="mt-4 flex flex-wrap gap-2">
     {OFFENCE_CATALOGUE.map(item=><button key={item.code} type="button" className={btnOutline+' !text-xs'} onClick={()=>{setFilters(f=>({...f,offence:item.label,status:'UNRESOLVED'}));setQuery(`Find unresolved ${item.label.toLowerCase()} cases`)}}>{item.label}</button>)}
    </div>
   </div>

   <div className="rounded-2xl border bg-white p-5 shadow-sm">
    <h3 className="font-semibold">{t('filtersTitle')}</h3>
    <p className="mt-1 text-xs text-slate-500">{t('purposeLabel')}: {inv?.purpose||defaultPurpose(user.role)}</p>
    <fieldset className="mt-3 grid gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
     {([['offence','Offence'],['status','Status'],['location','Location / station'],['crime_number','Crime number'],['case_number','Case number'],['date_from','Incident from'],['date_to','Incident to'],['person_name','Person name'],['person_role','Person role'],['act_code','Act code'],['section_code','Section code'],['police_unit','Police unit'],['district','District']] as const).map(([key,label])=>{
      const active=Boolean((filters as any)[key])
      return <label key={key} className="flex flex-col text-sm"><span className="mb-1 font-medium text-slate-600">{label}</span><input aria-label={label} className={`w-full rounded-lg border p-2 transition focus:ring-2 focus:ring-teal-300 ${active?'border-teal-400 bg-teal-50/40':'border-slate-200'}`} value={(filters as any)[key]} onChange={e=>setFilters({...filters,[key]:e.target.value})}/></label>
     })}
     <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm has-[:checked]:border-teal-400 has-[:checked]:bg-teal-50/40"><input type="checkbox" checked={hasArrest} onChange={e=>setHasArrest(e.target.checked)}/> Has arrest / surrender</label>
     <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm has-[:checked]:border-teal-400 has-[:checked]:bg-teal-50/40"><input type="checkbox" checked={hasChargesheet} onChange={e=>setHasChargesheet(e.target.checked)}/> Has chargesheet</label>
    </fieldset>
    <div className="mt-4">
     <p className="text-sm font-semibold">{t('sourcesLabel')}</p>
     <div className="mt-2 flex flex-wrap gap-2">
      {(control?.sources||[]).filter((s:Source)=>s.selectable!==false).map((s:Source)=><label key={s.id} className="rounded border px-2 py-1 text-xs"><input type="checkbox" checked={selected.includes(s.id)} onChange={e=>{const next=e.target.checked?[...selected,s.id]:selected.filter(id=>id!==s.id);setSelected(next);if(inv)void m3Api.updateSources(inv.id,next).then(setInv)}}/> {s.name||s.id}</label>)}
      {!control?.sources?.length&&<label className="rounded border px-2 py-1 text-xs"><input type="checkbox" checked={selected.includes('CCTNS_REPLICA')} onChange={()=>undefined}/> CCTNS_REPLICA</label>}
     </div>
    </div>
   </div>

   {preview&&<QueryInterpretationPanel preview={preview} onChange={setPreview}/>}

   <div className="rounded-2xl border bg-white p-5 shadow-sm">
    <div className="flex flex-wrap items-center justify-between gap-2">
     <h3 className="font-semibold">{t('resultsTitle')}</h3>
     {searched&&busy!=='search'&&<span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700">{results.length} {locale==='kn'?'ದಾಖಲೆಗಳು':results.length===1?'record':'records'}</span>}
    </div>
    {busy==='search'?<div className="mt-3 grid gap-3" role="status" aria-live="polite" aria-label={t('loading')}>
     {[0,1,2].map(i=><div key={i} className="rounded-xl border border-slate-200 p-4">
      <div className="h-4 w-2/5 rounded bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer"/>
      <div className="mt-3 flex gap-2"><div className="h-5 w-24 rounded-full bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer"/><div className="h-5 w-16 rounded-full bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer"/></div>
      <div className="mt-3 h-3 w-3/5 rounded bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer"/>
     </div>)}
    </div>:
     !searched?<p className="mt-2 text-sm text-slate-500">{t('resultsEmpty')}</p>:
     results.length===0?<p className="mt-2 text-sm text-amber-800">{locale==='kn'?'ಯಾವುದೇ ದಾಖಲೆ ಸಿಗಲಿಲ್ಲ. ಫಿಲ್ಟರ್ ವಿಸ್ತರಿಸಿ ಮತ್ತೆ ಹುಡುಕಿ.':'No authorised records matched. Broaden filters and search again.'}</p>:
     <div className="mt-3 grid gap-3">
      {results.map((item:any)=><article key={item.case_id||item.id} className="rounded-xl border border-slate-200 p-4 transition hover:border-teal-400 hover:shadow-md">
       <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
         <p className="font-semibold text-navy-950">{item.crime_number||item.fir_number} · {item.case_number||item.case_id}</p>
         <div className="mt-1 flex flex-wrap gap-2"><OffenceBadge offence={item.offence||item.category?.name}/><span className="text-xs text-slate-600">{item.canonical_status?.name||item.status}</span></div>
         <p className="mt-1 text-xs text-slate-500">{item.police_unit?.name||item.station_id} · {item.registered_at}</p>
        </div>
        <div className="flex flex-wrap gap-2">
         <button type="button" className={btnPrimary} onClick={()=>void openCase(item.case_id||item.id)}>{t('openCase360')}</button>
         <button type="button" className={btnOutline} onClick={()=>void showRelated(item.case_id||item.id)}>{t('related')}</button>
         <button type="button" className={btnOutline} onClick={()=>void showClusters(item.case_id||item.id)}>{t('networkClusters')}</button>
        </div>
       </div>
      </article>)}
     </div>}
   </div>
  </section>}

  {workspaceSection==='briefing'&&!isSupervisor&&<section className="grid gap-4">
   <div className="flex flex-wrap gap-2"><button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={()=>void loadBriefing()}>{busy==='briefing'?t('loading'):t('loadBriefing')}</button></div>
   {briefing?<ShiftBriefingPanel data={briefing}/>:<p className="rounded-xl border bg-white p-6 text-sm text-slate-600">{locale==='kn'?'ಬ್ರೀಫಿಂಗ್ ಲೋಡ್ ಮಾಡಿ.':'Load the shift briefing to fetch authorised attention leads.'}</p>}
  </section>}

  {workspaceSection==='trends'&&!isSupervisor&&<section className="grid gap-4">
   <div className="flex flex-wrap gap-2"><button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={()=>void loadTrends()}>{busy==='trends'?t('loading'):t('loadTrends')}</button></div>
   {trends?<CrimeTrendsPanel data={trends}/>:<p className="rounded-xl border bg-white p-6 text-sm text-slate-600">{locale==='kn'?'ಪ್ರವೃತ್ತಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಿ.':'Load crime trends for descriptive seasonality and MO co-occurrence.'}</p>}
  </section>}

  {workspaceSection==='chat'&&<section className="rounded-2xl border bg-white p-5 shadow-sm" aria-label="Chat assist">
   <h3 className="font-semibold">{t('chatAssist')}</h3>
   <p className="mt-1 text-sm text-slate-600">{locale==='kn'?'ಚಾಟ್ ವಿಭಾಗಗಳನ್ನು ತೆರೆಯುತ್ತದೆ — Case 360 ಅನ್ನು ಸ್ಕ್ರಾಲ್‌ನಲ್ಲಿ ಹಾಕುವುದಿಲ್ಲ.':'Chat opens portal sections and drawers — it does not dump Case 360 into an endless scroll.'}</p>
   <div className="mt-3 flex flex-wrap gap-2">{chatHelpPhrases.map(phrase=><button key={phrase} type="button" className={btnOutline+' !text-xs'} onClick={()=>void runChat(phrase)}>{phrase}</button>)}</div>
   <div className="mt-4 max-h-64 space-y-2 overflow-y-auto rounded-xl bg-slate-50 p-3">
    {chatLog.length===0?<p className="text-sm text-slate-500">{locale==='kn'?'ಇನ್ನೂ ಸಂದೇಶಗಳಿಲ್ಲ.':'No messages yet.'}</p>:chatLog.map(m=><div key={m.id} className={`rounded-lg px-3 py-2 text-sm ${m.role==='user'?'ml-8 bg-teal-700 text-white':'mr-8 bg-white border'}`}>{m.text}</div>)}
   </div>
   {pendingTranscript&&<div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm"><p className="font-semibold">Editable voice transcript</p><textarea className="mt-1 w-full rounded border p-2" value={pendingTranscript} onChange={e=>setPendingTranscript(e.target.value)}/><div className="mt-2 flex gap-2"><button type="button" className={btnPrimary} onClick={()=>{setChatInput(pendingTranscript);setPendingTranscript('');void runChat(pendingTranscript)}}>{t('confirm')}</button><button type="button" className={btnOutline} onClick={()=>setPendingTranscript('')}>{t('cancel')}</button></div></div>}
   <div className="mt-3 flex gap-2">
    <input aria-label="Ask ANVAYA" className="flex-1 rounded-xl border px-3 py-2" value={chatInput} onChange={e=>setChatInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')void runChat()}} placeholder={locale==='kn'?'ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಕೇಳಿ…':'Ask in English or Kannada…'}/>
    <button type="button" className={btnSecondary} onClick={()=>void startVoice()} aria-label="Voice">{recording?'⏹':'🎤'}</button>
    <button type="button" className={btnPrimary} disabled={Boolean(busy)} onClick={()=>void runChat()}>{t('send')}</button>
   </div>
  </section>}

  {caseOpen&&detail&&<PortalModal variant="drawer" title={`Case 360 · ${caseIdOf(detail)}`} onClose={()=>setCaseOpen(false)}>
   <div className="mb-4 flex flex-wrap gap-2">
    <button type="button" className={btnOutline} onClick={()=>void showRelated(caseIdOf(detail))}>{t('related')}</button>
    <button type="button" className={btnOutline} onClick={()=>void showGraph(caseIdOf(detail))}>{t('graph')}</button>
    <button type="button" className={btnOutline} onClick={()=>void showClusters(caseIdOf(detail))}>{t('networkClusters')}</button>
    <button type="button" className={btnOutline} onClick={()=>void showPriorities(caseIdOf(detail))}>{t('priorities')}</button>
    <button type="button" className={btnPrimary} onClick={()=>void prepareBrief(caseIdOf(detail))}>{t('prepareBrief')}</button>
   </div>
   <Case360Workspace detail={detail} onPassport={openPassport}/>
   {related&&<div className="mt-4"><RelatedCasesPanel data={related} onOpen={id=>void openCase(id)}/></div>}
   {graph&&<div className="mt-4"><FirRelationshipGraph data={graph} onOpen={id=>void openCase(id)}/></div>}
   {clusters&&<div className="mt-4"><NetworkClustersPanel data={clusters}/></div>}
   {priorities&&<div className="mt-4"><VerificationPriorityPanel data={priorities}/></div>}
   {detail.assurance&&<div className="mt-4"><RecordAssurancePanel data={detail.assurance} canResolve={user.role==='SUPERVISOR'} onUpdate={(findingId,status)=>{const id=caseIdOf(detail);if(!inv)return;void call('assurance',()=>m3Api.updateFirAssurance(inv.id,id,findingId,{status})).then(()=>m3Api.firAssurance(inv.id,id)).then(data=>data&&setDetail({...detail,assurance:data}))}}/></div>}
  </PortalModal>}

  {briefOpen&&brief&&<PortalModal variant="modal" title={t('downloadDossier')} onClose={()=>setBriefOpen(false)}>
   <BriefPreviewPanel data={brief} busy={busy==='brief-pdf'} onDownload={()=>void downloadBriefPdf()}/>
  </PortalModal>}

  {passport&&<SourcePassportDrawer passport={passport} onClose={()=>setPassport(null)}/>}
 </div>
}
