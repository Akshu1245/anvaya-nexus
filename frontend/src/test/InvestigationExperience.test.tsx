import {render,screen} from '@testing-library/react'
import {InvestigationExperience} from '../features/m4/InvestigationExperience'

it('renders the M4 authenticated investigation entry point without Base44 HTML',()=>{
  render(<InvestigationExperience/>)
  expect(screen.getByRole('heading',{name:'Demo Login'})).toBeInTheDocument()
  expect(screen.getByText(/server-side policy controls every factual response/i)).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Investigator'})).toBeInTheDocument()
})
