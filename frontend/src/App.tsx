import {useState} from 'react'
import {ApplicationShell,type PortalSection} from './components/ui'
import {ErrorBoundary} from './components/ErrorBoundary'
import {LocaleProvider} from './i18n/portal'
import {InvestigationPortal} from './features/portal/InvestigationPortal'

export function App() {
  const [section,setSection]=useState<PortalSection>('search')
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
