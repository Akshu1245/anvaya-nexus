import {useEffect,useState,type ReactNode} from 'react'

export type JourneyStage='ASK'|'DISCOVER'|'VERIFY'|'PRIORITISE'|'REPORT'
const stages:Array<{id:JourneyStage;label:string;description:string}>=[
 {id:'ASK',label:'Ask',description:'Interpret your question'},
 {id:'DISCOVER',label:'Discover',description:'Review returned FIRs'},
 {id:'VERIFY',label:'Verify',description:'Check cited evidence'},
 {id:'PRIORITISE',label:'Prioritise',description:'Plan human review'},
 {id:'REPORT',label:'Report',description:'Create cited brief'},
]

export function JourneyStepper({current,onSelect,maxReached}:{current:JourneyStage;onSelect?:(stage:JourneyStage)=>void;maxReached?:JourneyStage}){
 const order=stages.map(item=>item.id)
 const currentIndex=order.indexOf(current)
 const maxIndex=order.indexOf(maxReached||current)
 return <ol className="grid gap-2 overflow-x-auto pb-1 sm:grid-cols-5" aria-label="Investigation journey">{stages.map((item,index)=>{const state=index<currentIndex?'Complete':index===currentIndex?'Current':index<=maxIndex?'Available':'Locked';const clickable=Boolean(onSelect)&&index<=maxIndex;return <li key={item.id} aria-current={state==='Current'?'step':undefined}><button type="button" disabled={!clickable} onClick={()=>clickable&&onSelect?.(item.id)} className={`w-full min-w-36 rounded-xl border p-3 text-left ${state==='Current'?'border-teal-700 bg-teal-700 text-white':state==='Complete'||state==='Available'?'border-teal-200 bg-teal-50 text-teal-950 hover:bg-teal-100':'border-slate-200 bg-white text-slate-400'}`}><div className="flex justify-between gap-2"><b className="text-xs uppercase tracking-wide">{item.label}</b><span className="text-[10px]">{state}</span></div><p className="mt-1 text-xs">{item.description}</p></button></li>})}</ol>
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

const navItems=[
 {label:'Investigation Chat',target:'main-content'},
 {label:'About ANVAYA',target:'about-anvaya'},
 {label:'Helplines',target:'helplines'},
 {label:'Privacy',target:'privacy'},
 {label:'Screen Reader',target:'screen-reader'},
]

function scrollToSection(id:string){
 const el=document.getElementById(id)
 if(!el)return
 el.scrollIntoView({behavior:'smooth',block:'start'})
 if(el.tabIndex<0)el.tabIndex=-1
 el.focus({preventScroll:true})
}

const helplineEntries=[
 {icon:'🚨',label:'Emergency Response',number:'112'},
 {icon:'👮',label:'Police Control Room',number:'100'},
 {icon:'👩',label:'Women Helpline',number:'1091'},
 {icon:'🧒',label:'Child Helpline',number:'1098'},
 {icon:'💻',label:'Cyber Crime',number:'1930'},
 {icon:'🚦',label:'Traffic Helpline',number:'103'},
]

function AboutAnvayaSection(){
 return <section id="about-anvaya" aria-labelledby="about-anvaya-title" className="scroll-mt-6 border-t border-slate-200 bg-white">
  <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8">
   <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-teal-700">About ANVAYA</p>
   <h2 id="about-anvaya-title" className="mt-1 text-2xl font-bold text-navy-950">What we built, and why it matters</h2>
   <div className="mt-4 grid gap-6 lg:grid-cols-[2fr_1fr]">
    <div className="space-y-4 text-sm leading-6 text-slate-700">
     <p><b>ANVAYA</b> (ಅನ್ವಯ — "connection") is a conversational investigation-intelligence prototype built for the Karnataka State Police Datathon. Instead of forcing officers through separate menus for search, briefings, trends and reports, ANVAYA gives one chat surface: ask in plain language — typed or spoken — and it answers only from authorised synthetic FIR records, with a citation for every factual claim.</p>
     <p><b>What we built.</b> A grounded question-answering pipeline over a synthetic CCTNS-style dataset (FIRs, persons, vehicles, exhibits, documents, arrests and chargesheets); a Case 360 view that assembles the complete dossier for any case; shift briefings and descriptive crime-trend summaries (seasonality and modus-operandi patterns, never forecasts); candidate network clusters that connect related cases through recorded facts alone; and one-command exports — a cited Investigation Dossier PDF and a full conversation-transcript PDF, both watermarked as synthetic.</p>
     <p><b>What we integrated.</b> AI assist runs on OpenRouter free-tier open models with deterministic fallbacks, so the system stays useful even when no model responds. Optional multilingual voice (Kannada, Hindi, English) is powered by Sarvam AI speech and translation models. The frontend is React + Vite + Tailwind; the backend is Python with a SQLite synthetic store, deployable on Zoho Catalyst. Every AI-assisted answer passes a human-confirmation gate before anything is retrieved.</p>
     <p><b>Guardrails first.</b> No source, no factual claim. Sensitive identifiers are masked by policy, the system never infers guilt, risk or identity, and nothing here connects to live KSP or CCTNS systems. Every screen and export carries the synthetic-prototype notice, because trust is the feature.</p>
    </div>
    <div className="rounded-2xl border border-teal-100 bg-teal-50/60 p-5">
     <p className="text-xs font-bold uppercase tracking-wide text-teal-800">At a glance</p>
     <ul className="mt-3 space-y-2 text-sm text-teal-950">
      <li>• One chat for search, briefing, trends, Case 360 and reports</li>
      <li>• Citation-backed answers from synthetic FIR records only</li>
      <li>• Cited dossier PDF + conversation PDF exports</li>
      <li>• Candidate network clusters from recorded facts</li>
      <li>• OpenRouter free models with deterministic fallback</li>
      <li>• Kannada / Hindi / English voice via Sarvam AI (optional)</li>
      <li>• Human confirmation gate, masking, synthetic watermarks</li>
     </ul>
    </div>
   </div>
  </div>
 </section>
}

function HelplinesSection(){
 return <section id="helplines" aria-labelledby="helplines-title" className="scroll-mt-6 border-t border-slate-200 bg-navy-950">
  <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
   <h2 id="helplines-title" className="text-lg font-bold uppercase tracking-wide text-teal-300">Helplines</h2>
   <p className="mt-1 text-sm text-slate-400">These national helpline numbers are real and available 24×7. Everything else in this prototype is synthetic.</p>
   <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
    {helplineEntries.map(entry=><a key={entry.number} href={`tel:${entry.number}`} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center transition-colors hover:border-teal-400/60 hover:bg-white/10">
     <span className="text-2xl" aria-hidden>{entry.icon}</span>
     <p className="mt-1 text-3xl font-black leading-none text-white">{entry.number}</p>
     <p className="mt-2 text-sm font-semibold text-slate-300">{entry.label}</p>
    </a>)}
   </div>
  </div>
 </section>
}

export function ApplicationShell({children}:{children:ReactNode}){
 const [online,setOnline]=useState(()=>navigator.onLine)
 const today=new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long',year:'numeric'})
 useEffect(()=>{const up=()=>setOnline(true),down=()=>setOnline(false);window.addEventListener('online',up);window.addEventListener('offline',down);return()=>{window.removeEventListener('online',up);window.removeEventListener('offline',down)}},[])
 return <div className="min-h-screen bg-[#eef2f4] text-slate-950">
  <a href="#main-content" className="sr-only z-50 rounded bg-white px-4 py-3 font-semibold text-navy-950 focus:not-sr-only focus:absolute focus:left-4 focus:top-4">Skip to workspace</a>

  {/* Government top strip */}
  <div className="bg-navy-950 text-[11px] text-slate-300">
   <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-5 py-1.5 sm:px-8">
    <span className="font-medium tracking-wide">ಕರ್ನಾಟಕ ಸರ್ಕಾರ · Government of Karnataka</span>
    <span className="flex flex-wrap items-center gap-3">
     <span className="hidden sm:inline">{today}</span>
     <button type="button" onClick={()=>scrollToSection('screen-reader')} className="hidden border-l border-slate-600 pl-3 hover:text-white sm:inline">Screen Reader Access</button>
     <span className="border-l border-slate-600 pl-3 font-semibold text-teal-300">ಕನ್ನಡ | English</span>
    </span>
   </div>
  </div>

  {/* Main portal header */}
  <header className="border-b-4 border-[#c9a227] bg-white shadow-sm">
   <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
    <div className="flex items-center gap-4">
     <KspEmblem/>
     <div className="animate-fade-in">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್</p>
      <p className="text-xl font-bold leading-tight text-navy-950 sm:text-2xl">Karnataka State Police</p>
      <h1 className="mt-0.5 text-sm font-semibold text-teal-700">Investigation Intelligence Prototype</h1>
      <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Ask. Discover. Verify. Brief.</h2>
     </div>
    </div>
    <div className="flex items-center gap-3">
     <div className="hidden rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-center md:block">
      <p className="text-[10px] font-bold uppercase tracking-wide text-red-700">Emergency</p>
      <p className="text-2xl font-black leading-none text-red-700">112</p>
     </div>
     <div className="rounded-xl bg-gradient-to-br from-navy-900 to-teal-900 px-4 py-2 text-white shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-teal-300">ANVAYA</p>
      <p className="text-sm font-semibold leading-tight">Investigation Intelligence Prototype</p>
     </div>
     <span aria-live="polite" className={online?'hidden rounded-full border border-teal-600/40 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800 lg:inline':'rounded-full border border-amber-400 bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-950'}>{online?'● Online':'Offline — data access paused'}</span>
    </div>
   </div>
   {/* Navigation bar */}
   <nav aria-label="Portal navigation" className="bg-navy-950">
    <div className="mx-auto flex max-w-7xl items-center gap-1 overflow-x-auto px-5 sm:px-8">
     {navItems.map((item,index)=><button key={item.label} type="button" onClick={()=>scrollToSection(item.target)} className={`whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide transition-colors ${index===0?'border-b-2 border-teal-300 bg-white/5 text-teal-300':'text-slate-300 hover:bg-white/5 hover:text-white'}`}>{item.label}</button>)}
    </div>
   </nav>
   {/* Helpline ticker strip */}
   <div className="border-t border-slate-200 bg-slate-50">
    <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-1 px-5 py-2 text-sm text-slate-700 sm:px-8">
     <button type="button" onClick={()=>scrollToSection('helplines')} className="font-bold uppercase tracking-wide text-navy-900 underline decoration-teal-500 decoration-2 underline-offset-4 hover:text-teal-700">Helplines</button>
     <span>🚨 Emergency <b className="text-base text-red-700">112</b></span>
     <span>👮 Police Control <b className="text-base">100</b></span>
     <span>👩 Women <b className="text-base">1091</b></span>
     <span>🧒 Child <b className="text-base">1098</b></span>
     <span>💻 Cyber Crime <b className="text-base">1930</b></span>
     <span className="hidden sm:inline">🚦 Traffic <b className="text-base">103</b></span>
    </div>
   </div>
  </header>

  <div role="note" className="border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-center text-[11px] font-bold tracking-[0.12em] text-amber-950">SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE</div>

  {!online&&<p role="status" className="border-b border-amber-300 bg-amber-50 px-5 py-3 text-center text-sm text-amber-950">Your typed question remains on screen, but ANVAYA will not retrieve, cache or change FIR data while offline. Reconnect and retry manually.</p>}

  <main id="main-content" tabIndex={-1} className="mx-auto max-w-7xl animate-fade-in px-5 py-7 outline-none sm:px-8 sm:py-8">{children}</main>

  <AboutAnvayaSection/>
  <HelplinesSection/>

  {/* Portal footer */}
  <footer className="mt-10 bg-navy-950 text-slate-300">
   <div className="mx-auto grid max-w-7xl gap-8 px-5 py-10 sm:grid-cols-2 sm:px-8 lg:grid-cols-4">
    <div>
     <div className="flex items-center gap-3"><KspEmblem/><div><p className="font-bold text-white">Karnataka State Police</p><p className="text-xs text-slate-400">ANVAYA Investigation Portal</p></div></div>
     <p className="mt-3 text-xs leading-5 text-slate-400">ANVAYA is a synthetic conversational investigation-intelligence prototype built for a datathon demonstration. It is not connected to live KSP or CCTNS systems and every output requires human review.</p>
     <button type="button" onClick={()=>scrollToSection('about-anvaya')} className="mt-3 text-xs font-semibold text-teal-300 underline underline-offset-2 hover:text-white">Read more about ANVAYA →</button>
    </div>
    <div id="screen-reader" className="scroll-mt-4">
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">Quick Links</p>
     <p className="mt-2 text-xs leading-5 text-slate-400">Screen-reader landmarks, keyboard navigation and a skip link are available throughout this prototype.</p>
     <ul className="mt-3 space-y-2 text-xs">
      {['Investigation Chat','Shift Briefing','Crime Trends','Source Passports','Case 360 View','Cited Case Briefs'].map(link=><li key={link}><button type="button" onClick={()=>scrollToSection('main-content')} className="text-slate-300 transition-colors hover:text-teal-300">{link}</button></li>)}
     </ul>
    </div>
    <div>
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">Helplines</p>
     <ul className="mt-3 space-y-2 text-sm">
      {helplineEntries.map(entry=><li key={entry.number}>{entry.label} — <b className="text-base text-white">{entry.number}</b></li>)}
     </ul>
     <button type="button" onClick={()=>scrollToSection('helplines')} className="mt-3 text-xs font-semibold text-teal-300 underline underline-offset-2 hover:text-white">View all helplines →</button>
    </div>
    <div id="privacy" className="scroll-mt-4">
     <p className="text-sm font-bold uppercase tracking-wide text-teal-300">Headquarters</p>
     <p className="mt-3 text-xs leading-5">Office of the Director General &amp; Inspector General of Police,<br/>Nrupathunga Road,<br/>Bengaluru — 560001, Karnataka</p>
     <p className="mt-3 text-xs text-slate-400">Prototype build 2.4.1 · Synthetic datathon evaluation</p>
     <p className="mt-3 text-xs leading-5 text-slate-400">Privacy: do not enter personal or operational information. This interface is for synthetic demonstration data only.</p>
    </div>
   </div>
   <div className="border-t border-white/10">
    <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-5 py-3 text-[11px] text-slate-400 sm:px-8">
     <span>© 2026 Karnataka State Police · KSP Datathon Prototype</span>
     <span className="flex gap-4">{[
      {label:'Privacy Policy',target:'privacy'},
      {label:'Terms of Use',target:'privacy'},
      {label:'About',target:'about-anvaya'},
      {label:'Helplines',target:'helplines'},
     ].map(link=><button key={link.label} type="button" onClick={()=>scrollToSection(link.target)} className="transition-colors hover:text-teal-300">{link.label}</button>)}</span>
    </div>
    <p className="mx-auto max-w-7xl px-5 pb-5 text-[11px] leading-5 text-slate-500 sm:px-8">No source, no factual claim. No verification, no confirmed connection. ANVAYA has no live KSP/CCTNS connection and makes no identity, guilt, risk or operational decision. Static app resources may be cached for resilience; FIR data and API responses are never stored offline.</p>
   </div>
  </footer>
 </div>
}
