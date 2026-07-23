import {useEffect,useState} from 'react'
import {ApplicationShell,type PortalSection} from './components/ui'
import {ErrorBoundary} from './components/ErrorBoundary'
import {LocaleProvider} from './i18n/portal'
import {InvestigationPortal} from './features/portal/InvestigationPortal'

const VALID_SECTIONS:readonly PortalSection[]=['search','briefing','trends','chat','about','helplines','privacy','screen-reader']

const SECTION_TITLES:Record<PortalSection,string>={
  search:'Search & Case 360',
  briefing:'Shift Briefing',
  trends:'Crime Trends',
  chat:'Investigation Chat',
  about:'About ANVAYA',
  helplines:'Helplines',
  privacy:'Privacy & Contact',
  'screen-reader':'Screen Reader Support',
}

function readInitialSection():PortalSection{
  if(typeof window==='undefined')return 'search'
  try{
    const params=new URLSearchParams(window.location.search)
    const q=params.get('section') as PortalSection|null
    if(q&&VALID_SECTIONS.includes(q))return q
    const path=window.location.pathname.replace(/^\/+/,'').replace(/\/$/,'') as PortalSection
    if(path&&VALID_SECTIONS.includes(path))return path
  }catch{/* ignore */}
  return 'search'
}

export function App() {
  const [section,setSection]=useState<PortalSection>(()=>readInitialSection())

  // Sync URL <-> section for deep links and browser back/forward
  useEffect(()=>{
    if(typeof window==='undefined')return
    const desired=`?section=${section}`
    if(window.location.search!==desired){
      try{window.history.replaceState({section},'',desired+window.location.hash)}catch{/* ignore */}
    }
    document.title=`ANVAYA · ${SECTION_TITLES[section]} — Karnataka State Police`
  },[section])

  useEffect(()=>{
    if(typeof window==='undefined')return
    const onPop=()=>setSection(readInitialSection())
    window.addEventListener('popstate',onPop)
    return ()=>window.removeEventListener('popstate',onPop)
  },[])

  return (
    <ErrorBoundary>
      <LocaleProvider>
        <ApplicationShell activeSection={section} onNavigate={setSection}>
          <InvestigationPortal section={section} onSectionChange={setSection}/>
        </ApplicationShell>
      </LocaleProvider>
    </ErrorBoundary>
  )
}
