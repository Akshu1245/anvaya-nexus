import {useEffect,useState,type ReactNode} from 'react'
import {useLocale,type Locale} from '../i18n/portal'
import {btnDanger,btnOutline} from './PortalButtons'
import {AppLayout} from './AppLayout'

export type JourneyStage='ASK'|'DISCOVER'|'VERIFY'|'PRIORITISE'|'REPORT'
export type PortalSection='search'|'briefing'|'trends'|'chat'|'about'|'helplines'|'privacy'|'screen-reader'

const stages:Array<{id:JourneyStage;label:string;description:string}>=[
 {id:'ASK',label:'Ask',description:'Interpret your question'},
 {id:'DISCOVER',label:'Discover',description:'Review returned FIRs'},
 {id:'VERIFY',label:'Verify',description:'Check cited evidence'},
 {id:'PRIORITISE',label:'Prioritise',description:'Plan human review'},
 {id:'REPORT',label:'Report',description:'Create cited brief'},
]

function JourneyStageIcon({kind}:{kind:JourneyStage}){
 const common={width:18,height:18,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','strokeWidth':1.8,'strokeLinecap':'round' as const,'strokeLinejoin':'round' as const,'aria-hidden':true}
 if(kind==='ASK')return <svg {...common}><path d="M5 5h14v10H9l-4 4z"/><path d="M8 9h8M8 12h5"/></svg>
 if(kind==='DISCOVER')return <svg {...common}><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.3-4.3"/></svg>
 if(kind==='VERIFY')return <svg {...common}><path d="M12 3l8 3v6c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/></svg>
 if(kind==='PRIORITISE')return <svg {...common}><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>
 return <svg {...common}><path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4"/><path d="M10 12h6M10 15h6M10 18h4"/></svg>
}

export function JourneyStepper({current,onSelect,maxReached}:{current:JourneyStage;onSelect?:(stage:JourneyStage)=>void;maxReached?:JourneyStage}){
 const order=stages.map(item=>item.id)
 const currentIndex=order.indexOf(current)
 const maxIndex=order.indexOf(maxReached||current)
 return <ol className="grid grid-cols-1 gap-2 sm:grid-cols-5 sm:gap-0" aria-label="Investigation journey">{stages.map((item,index)=>{
  const state=index<currentIndex?'Complete':index===currentIndex?'Current':'Available'
  const clickable=Boolean(onSelect)
  const badge=state==='Complete'?'border-transparent bg-teal-600 text-white':state==='Current'?'border-teal-400 bg-navy-900 text-white ring-2 ring-teal-300 ring-offset-2 ring-offset-white':'border-teal-300 bg-white text-teal-700'
  const pill=state==='Complete'?'bg-teal-50 text-teal-700':state==='Current'?'bg-navy-900 text-teal-100':'bg-teal-50 text-teal-600'
  const glyph=state==='Complete'?'✓':<JourneyStageIcon kind={item.id}/>
  return <li key={item.id} aria-current={state==='Current'?'step':undefined} className="relative flex flex-col">
   {index>0&&<span aria-hidden className={`absolute left-0 top-5 hidden h-0.5 w-full -translate-x-1/2 sm:block ${index<=currentIndex?'bg-teal-500':'bg-slate-200'}`}/>}
   <button type="button" disabled={!clickable} onClick={()=>clickable&&onSelect?.(item.id)} className={`btn-portal group flex w-full flex-row items-center gap-3 rounded-xl p-3 text-left sm:flex-col sm:items-center sm:gap-2 sm:text-center`}>
    <span aria-hidden className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-base shadow-sm transition ${badge}`}>{glyph}</span>
    <span className="flex min-w-0 flex-col sm:items-center">
     <b className="text-xs font-semibold uppercase tracking-wide text-navy-950">{item.label}</b>
     <span className="mt-0.5 text-[11px] leading-tight text-slate-700">{item.description}</span>
     <span className={`mt-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${pill}`}>{state}</span>
    </span>
   </button>
  </li>})}</ol>
}

function KspEmblem(){
 return <svg viewBox="0 0 64 64" className="h-14 w-14 shrink-0" role="img" aria-label="Karnataka State Police emblem (prototype)">
  <defs><linearGradient id="shieldGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1f4368"/><stop offset="100%" stopColor="#07111f"/></linearGradient></defs>
  <path d="M32 3 L56 11 V30 C56 45 46 56 32 61 C18 56 8 45 8 30 V11 Z" fill="url(#shieldGrad)" stroke="#c9a227" strokeWidth="2.4"/>
  <path d="M32 9 L50 15 V29.5 C50 41.5 42 50.3 32 54.5 C22 50.3 14 41.5 14 29.5 V15 Z" fill="none" stroke="#70c5c5" strokeWidth="1.1" opacity="0.7"/>
  <circle cx="32" cy="27" r="8.5" fill="none" stroke="#c9a227" strokeWidth="1.6"/>
  <path d="M32 20.5 L33.9 24.8 L38.6 25.2 L35 28.2 L36.1 32.8 L32 30.3 L27.9 32.8 L29 28.2 L25.4 25.2 L30.1 24.8 Z" fill="#c9a227"/>
  <text x="32" y="46" textAnchor="middle" fontSize="8.5" fontWeight="700" fill="#e9f0f2" fontFamily="Inter,sans-serif">KSP</text>
 </svg>
}

export function scrollToSection(id:string){
 const el=document.getElementById(id)
 if(!el)return
 el.scrollIntoView({behavior:'smooth',block:'start'})
 if(el.tabIndex<0)el.tabIndex=-1
 try{el.focus({preventScroll:true})}catch{/* ignore */}
}

function HelplineIcon({kind}:{kind:string}){
 const common={width:24,height:24,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','strokeWidth':1.8,'strokeLinecap':'round' as const,'strokeLinejoin':'round' as const,'aria-hidden':true}
 if(kind==='emergency')return <svg {...common}><path d="M12 3l9 4.5v5c0 5-3.9 8.5-9 9-5.1-.5-9-4-9-9v-5L12 3z"/><path d="M12 8v5"/><circle cx="12" cy="16" r=".8" fill="currentColor"/></svg>
 if(kind==='police')return <svg {...common}><path d="M4 10c0-3.5 3.6-6 8-6s8 2.5 8 6v3H4v-3z"/><path d="M4 13h16"/><circle cx="12" cy="8" r="1.2" fill="currentColor"/></svg>
 if(kind==='women')return <svg {...common}><circle cx="12" cy="8" r="4"/><path d="M12 12v8M9 17h6"/></svg>
 if(kind==='child')return <svg {...common}><circle cx="12" cy="8" r="4"/><path d="M8 20c0-2.5 1.8-4 4-4s4 1.5 4 4"/><circle cx="10.5" cy="8" r=".6" fill="currentColor"/><circle cx="13.5" cy="8" r=".6" fill="currentColor"/></svg>
 if(kind==='cyber')return <svg {...common}><rect x="3" y="5" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 17v3"/><path d="M8 10l-2 2 2 2M16 10l2 2-2 2M14 9l-4 6"/></svg>
 if(kind==='traffic')return <svg {...common}><rect x="8" y="3" width="8" height="18" rx="2"/><circle cx="12" cy="7" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="17" r="1.4"/></svg>
 return null
}

const helplineEntries=[
 {kind:'emergency',labelKey:'Emergency Response',labelKn:'ತುರ್ತು ಪ್ರತಿಕ್ರಿಯೆ',number:'112'},
 {kind:'police',labelKey:'Police Control Room',labelKn:'ಪೊಲೀಸ್ ನಿಯಂತ್ರಣ ಕೊಠಡಿ',number:'100'},
 {kind:'women',labelKey:'Women Helpline',labelKn:'ಮಹಿಳಾ ಸಹಾಯವಾಣಿ',number:'1091'},
 {kind:'child',labelKey:'Child Helpline',labelKn:'ಮಕ್ಕಳ ಸಹಾಯವಾಣಿ',number:'1098'},
 {kind:'cyber',labelKey:'Cyber Crime',labelKn:'ಸೈಬರ್ ಅಪರಾಧ',number:'1930'},
 {kind:'traffic',labelKey:'Traffic Helpline',labelKn:'ಸಂಚಾರ ಸಹಾಯವಾಣಿ',number:'103'},
]

function AboutAnvayaSection({locale}:{locale:Locale}){
 const {t}=useLocale()
 return <section id="about-anvaya" tabIndex={-1} aria-labelledby="about-anvaya-title" className="scroll-mt-6 border-t border-slate-200 bg-white outline-none">
  <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8">
   <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-teal-700">{t('nav.about')}</p>
   <h2 id="about-anvaya-title" className="mt-1 text-2xl font-bold text-navy-950">{t('aboutTitle')}</h2>
   <div className="mt-4 grid gap-6 lg:grid-cols-[2fr_1fr]">
    <div className="space-y-4 text-sm leading-6 text-slate-700">
     <p>{t('aboutLead')}</p>
     {locale==='kn'
      ?<>
        <p><b>ನಾವು ನಿರ್ಮಿಸಿದ್ದು.</b> ಸಂಶ್ಲೇಷಿತ CCTNS-ಶೈಲಿ FIR ದತ್ತಾಂಶದ ಮೇಲೆ ಆಧಾರಿತ ಪ್ರಶ್ನೋತ್ತರ, Case 360 ಡಾಸಿಯರ್, ಶಿಫ್ಟ್ ಬ್ರೀಫಿಂಗ್, ವಿವರಣಾತ್ಮಕ ಪ್ರವೃತ್ತಿಗಳು, ಅಭ್ಯರ್ಥಿ ನೆಟ್‌ವರ್ಕ್ ಕ್ಲಸ್ಟರ್‌ಗಳು ಮತ್ತು ಉಲ್ಲೇಖಿತ PDF ರಫ್ತುಗಳು.</p>
        <p><b>ಸಂಯೋಜನೆಗಳು.</b> OpenRouter ಉಚಿತ ಮಾದರಿಗಳು, ಐಚ್ಛಿಕ ಸರ್ವಮ್ ಧ್ವನಿ (ಕನ್ನಡ/ಹಿಂದಿ/ಇಂಗ್ಲಿಷ್), React + Vite + Tailwind, Python + SQLite, Zoho Catalyst ನಿಯೋಜನೆ.</p>
        <p><b>ರಕ್ಷಣಾ ಗೇಟ್‌ಗಳು.</b> ಮೂಲವಿಲ್ಲದೆ ಹಕ್ಕು ಇಲ್ಲ; ಮಾಸ್ಕಿಂಗ್; ಮಾನವ ದೃಢೀಕರಣ; ಲೈವ್ KSP/CCTNS ಸಂಪರ್ಕವಿಲ್ಲ.</p>
       </>
      :<>
        <p><b>What we built.</b> Grounded Q&amp;A over synthetic CCTNS-style FIR data; Case 360 dossiers; shift briefings; descriptive seasonality and MO trends (never forecasts); candidate network clusters from recorded facts; cited Investigation Dossier and conversation PDFs.</p>
        <p><b>What we integrated.</b> OpenRouter free-tier models with deterministic fallbacks; optional Sarvam AI multilingual voice; React + Vite + Tailwind; Python + SQLite on Zoho Catalyst. Every AI-assisted answer passes a human-confirmation gate.</p>
        <p><b>Guardrails first.</b> No source, no factual claim. Masking by policy. Never infers guilt, risk or identity. No live KSP or CCTNS connection.</p>
       </>}
    </div>
    <div className="rounded-2xl border border-teal-100 bg-teal-50/60 p-5">
     <p className="text-xs font-bold uppercase tracking-wide text-teal-800">{locale==='kn'?'ಸಂಕ್ಷಿಪ್ತ ನೋಟ':'At a glance'}</p>
     <ul className="mt-3 space-y-2 text-sm text-teal-950">
      <li>• {locale==='kn'?'ಫಾರ್ಮ್-ಮೊದಲು ಹುಡುಕಾಟ + ಚಾಟ್ ಸಹಾಯ':'Form-first search + chat assist'}</li>
      <li>• {locale==='kn'?'ಮೂಲ-ಉಲ್ಲೇಖಿತ ಉತ್ತರಗಳು':'Citation-backed answers'}</li>
      <li>• {locale==='kn'?'ಡಾಸಿಯರ್ PDF + ಸಂಭಾಷಣೆ PDF':'Dossier PDF + conversation PDF'}</li>
      <li>• {locale==='kn'?'ಅಭ್ಯರ್ಥಿ ನೆಟ್‌ವರ್ಕ್ ಕ್ಲಸ್ಟರ್‌ಗಳು':'Candidate network clusters'}</li>
      <li>• {locale==='kn'?'ಕನ್ನಡ / ಇಂಗ್ಲಿಷ್ UI · ಧ್ವನಿ ಐಚ್ಛಿಕ':'English + Kannada UI · voice optional'}</li>
     </ul>
    </div>
   </div>
  </div>
 </section>
}

function HelplinesSection({locale}:{locale:Locale}){
 const {t}=useLocale()
 return <section id="helplines" tabIndex={-1} aria-labelledby="helplines-title" className="scroll-mt-6 border-t border-slate-200 bg-navy-950 outline-none">
  <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
   <h2 id="helplines-title" className="text-lg font-bold uppercase tracking-wide text-teal-300">{t('helplinesTitle')}</h2>
   <p className="mt-1 text-sm text-slate-400">{t('helplinesLead')}</p>
   <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
    {helplineEntries.map(entry=><a key={entry.number} href={`tel:${entry.number}`} className={`${btnDanger} flex-col !h-auto !py-4 text-center`}>
     <span className="flex items-center justify-center text-white" aria-hidden><HelplineIcon kind={entry.kind}/></span>
     <p className="mt-1 text-3xl font-black leading-none">{entry.number}</p>
     <p className="mt-2 text-sm font-semibold text-red-100">{locale==='kn'?entry.labelKn:entry.labelKey}</p>
    </a>)}
   </div>
  </div>
 </section>
}

type ShellProps={
 children:ReactNode
 activeSection?:PortalSection
 onNavigate?:(section:PortalSection)=>void
}

export function ApplicationShell({children,activeSection='search',onNavigate}:ShellProps){
 const {locale,setLocale,t}=useLocale()
 const [online,setOnline]=useState(()=>navigator.onLine)
 const today=new Date().toLocaleDateString(locale==='kn'?'kn-IN':'en-IN',{weekday:'long',day:'numeric',month:'long',year:'numeric'})
 useEffect(()=>{const up=()=>setOnline(true),down=()=>setOnline(false);window.addEventListener('online',up);window.addEventListener('offline',down);return()=>{window.removeEventListener('online',up);window.removeEventListener('offline',down)}},[])

 const go=(section:PortalSection)=>{
  onNavigate?.(section)
  if(section==='about'||section==='helplines'||section==='privacy'||section==='screen-reader'){
   const id=section==='screen-reader'?'screen-reader':section==='about'?'about-anvaya':section
   requestAnimationFrame(()=>scrollToSection(id))
  }else{
   requestAnimationFrame(()=>scrollToSection('main-content'))
  }
 }

 const navItems:Array<{label:string;section:PortalSection}>=[
  {label:t('nav.search'),section:'search'},
  {label:t('nav.briefing'),section:'briefing'},
  {label:t('nav.trends'),section:'trends'},
  {label:t('nav.chat'),section:'chat'},
  {label:t('nav.about'),section:'about'},
  {label:t('nav.helplines'),section:'helplines'},
 ]

 return <div className="min-h-screen bg-[#eef2f4] text-slate-950">
  <a href="#main-content" className="sr-only z-50 rounded bg-white px-4 py-3 font-semibold text-navy-950 focus:not-sr-only focus:absolute focus:left-4 focus:top-4">{t('skipWorkspace')}</a>

  <div className="bg-navy-950 text-[11px] text-slate-300">
   <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-5 py-1.5 sm:px-8">
    <span className="font-medium tracking-wide">ಕರ್ನಾಟಕ ಸರ್ಕಾರ · Government of Karnataka</span>
    <span className="flex flex-wrap items-center gap-3">
     <span className="hidden sm:inline">{today}</span>
     <button type="button" onClick={()=>go('screen-reader')} className="hidden border-l border-slate-600 pl-3 hover:text-white sm:inline">{t('nav.screenReader')}</button>
     <span className="flex items-center gap-1 border-l border-slate-600 pl-3" role="group" aria-label="Language">
      <button type="button" aria-pressed={locale==='kn'} onClick={()=>setLocale('kn')} className={`btn-portal rounded px-2 py-0.5 font-semibold ${locale==='kn'?'bg-teal-700 text-white':'text-teal-300 hover:text-white'}`}>{t('kannada')}</button>
      <span aria-hidden>|</span>
      <button type="button" aria-pressed={locale==='en'} onClick={()=>setLocale('en')} className={`btn-portal rounded px-2 py-0.5 font-semibold ${locale==='en'?'bg-teal-700 text-white':'text-teal-300 hover:text-white'}`}>{t('english')}</button>
     </span>
    </span>
   </div>
  </div>

  <header className="border-b-4 border-[#c9a227] bg-white shadow-sm">
   <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
    <div className="flex items-center gap-4">
     <KspEmblem/>
     <div className="animate-fade-in">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್</p>
      <p className="text-xl font-bold leading-tight text-navy-950 sm:text-2xl">Karnataka State Police</p>
      <h1 className="mt-0.5 text-sm font-semibold text-teal-700">{locale==='kn'?'ತನಿಖಾ ಬುದ್ಧಿಮತ್ತೆ ಮಾದರಿ':'Investigation Intelligence Prototype'}</h1>
      <h2 className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.14em] text-slate-600">{locale==='kn'?'ಕೇಳಿ. ಕಂಡುಹಿಡಿಯಿರಿ. ಪರಿಶೀಲಿಸಿ. ವರದಿ.':'Ask. Discover. Verify. Brief.'}</h2>
     </div>
    </div>
    <div className="flex items-center gap-3">
     <a href="tel:112" aria-label={`${t('emergency')} 112`} className={`${btnDanger} hidden !px-3 !py-1.5 md:inline-flex md:items-center md:gap-2`}>
      <HelplineIcon kind="emergency"/>
      <span className="flex flex-col leading-none text-left"><span className="text-[9px] font-bold uppercase tracking-wide opacity-90">{t('emergency')}</span><span className="text-base font-black leading-none">112</span></span>
     </a>
     <div className="rounded-xl bg-gradient-to-br from-navy-900 to-teal-900 px-4 py-2 text-white shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-teal-300">ANVAYA</p>
      <p className="text-sm font-semibold leading-tight">{locale==='kn'?'ತನಿಖಾ ಪೋರ್ಟಲ್':'Investigation Portal'}</p>
     </div>
     <span aria-live="polite" className={online?'hidden rounded-full border border-teal-600/40 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800 lg:inline':'rounded-full border border-amber-400 bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-950'}>{online?t('online'):t('offline')}</span>
    </div>
   </div>
   <nav aria-label="Portal navigation" className="bg-navy-950">
    <div className="mx-auto flex max-w-7xl items-center gap-1 overflow-x-auto px-5 sm:px-8">
     {navItems.map(item=>{
      const active=activeSection===item.section||(item.section==='about'&&activeSection==='about')
      return <button key={item.section} type="button" onClick={()=>go(item.section)} className={`btn-portal whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide ${active?'border-b-2 border-teal-300 bg-white/5 text-teal-300':'text-slate-300 hover:bg-white/5 hover:text-white'}`}>{item.label}</button>
     })}
    </div>
   </nav>
  </header>

  <div role="note" className="sticky top-0 z-40 border-b border-amber-200 bg-amber-50/95 px-4 py-1.5 text-center text-xs font-bold tracking-[0.12em] text-amber-950 shadow-sm backdrop-blur sm:text-sm">{t('prototypeBanner')}</div>

  {!online&&<p role="status" className="border-b border-amber-300 bg-amber-50 px-5 py-3 text-center text-sm text-amber-950">{t('offline')}</p>}

  <AppLayout isConversational={activeSection==='chat'}>
   <main id="main-content" tabIndex={-1} className={activeSection==='chat'?'h-full outline-none':'mx-auto max-w-7xl animate-fade-in px-5 py-7 outline-none sm:px-8 sm:py-8'}>{children}</main>
  </AppLayout>

  <AboutAnvayaSection locale={locale}/>
  <HelplinesSection locale={locale}/>

  <footer className="mt-10 bg-navy-950 text-slate-300">
   <div className="mx-auto grid max-w-7xl gap-8 px-5 py-10 sm:grid-cols-2 sm:px-8 lg:grid-cols-4">
    <div>
     <div className="flex items-center gap-3"><KspEmblem/><div><p className="font-bold text-white">Karnataka State Police</p><p className="text-xs text-slate-400">ANVAYA Investigation Portal</p></div></div>
     <p className="mt-3 text-sm leading-6 text-slate-400">{t('aboutLead')}</p>
     <button type="button" onClick={()=>go('about')} className={`${btnOutline} mt-3 !border-teal-400/40 !bg-transparent !text-teal-300`}>{t('nav.about')} →</button>
    </div>
    <div id="screen-reader" tabIndex={-1} className="scroll-mt-4 outline-none">
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">{locale==='kn'?'ತ್ವರಿತ ಲಿಂಕ್‌ಗಳು':'Quick Links'}</p>
     <p className="mt-2 text-sm leading-6 text-slate-400">{locale==='kn'?'ಸ್ಕ್ರೀನ್-ರೀಡರ್ ಲ್ಯಾಂಡ್‌ಮಾರ್ಕ್‌ಗಳು ಮತ್ತು ಕೀಬೋರ್ಡ್ ನ್ಯಾವಿಗೇಷನ್ ಲಭ್ಯವಿದೆ.':'Screen-reader landmarks, keyboard navigation and a skip link are available throughout this prototype.'}</p>
     <ul className="mt-3 space-y-2 text-sm">
      {([
       ['nav.search','search'],
       ['nav.briefing','briefing'],
       ['nav.trends','trends'],
       ['nav.chat','chat'],
      ] as const).map(([key,section])=><li key={section}><button type="button" onClick={()=>go(section)} className="text-slate-300 transition-colors hover:text-teal-300">{t(key)}</button></li>)}
     </ul>
    </div>
    <div>
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">{t('helplinesTitle')}</p>
     <ul className="mt-3 space-y-2 text-sm">
      {helplineEntries.map(entry=><li key={entry.number}><a href={`tel:${entry.number}`} className="hover:text-teal-300">{locale==='kn'?entry.labelKn:entry.labelKey} — <b className="text-base text-white">{entry.number}</b></a></li>)}
     </ul>
     <button type="button" onClick={()=>go('helplines')} className="mt-3 text-sm font-semibold text-teal-300 underline underline-offset-2 hover:text-white">{t('nav.helplines')} →</button>
    </div>
    <div id="privacy" tabIndex={-1} className="scroll-mt-4 outline-none">
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">{t('privacyTitle')}</p>
     <p className="mt-3 text-sm leading-6">Office of the Director General &amp; Inspector General of Police,<br/>Nrupathunga Road,<br/>Bengaluru — 560001, Karnataka</p>
     <p className="mt-3 text-sm leading-6 text-slate-400">{t('privacyBody')}</p>
    </div>
   </div>
   <div className="border-t border-white/10">
    <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-5 py-3 text-xs text-slate-400 sm:px-8">
     <span>© 2026 Karnataka State Police · KSP Datathon Prototype</span>
     <span className="flex gap-4">
      <button type="button" onClick={()=>go('privacy')} className="hover:text-teal-300">{t('nav.privacy')}</button>
      <button type="button" onClick={()=>go('about')} className="hover:text-teal-300">{t('nav.about')}</button>
      <button type="button" onClick={()=>go('helplines')} className="hover:text-teal-300">{t('nav.helplines')}</button>
     </span>
    </div>
    <p className="mx-auto max-w-7xl px-5 pb-5 text-xs leading-5 text-slate-300 sm:px-8">No source, no factual claim. No verification, no confirmed connection. ANVAYA has no live KSP/CCTNS connection and makes no identity, guilt, risk or operational decision.</p>
   </div>
  </footer>
 </div>
}
