import { ConversationExperience } from './features/m4/ConversationExperience'
import {ApplicationShell} from './components/ui'
import {ErrorBoundary} from './components/ErrorBoundary'

export function App() {
  return <ErrorBoundary><ApplicationShell><ConversationExperience /></ApplicationShell></ErrorBoundary>
}
