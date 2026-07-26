import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

const roles = [
  { id: 'INVESTIGATOR', label: 'Investigator', description: 'Handle active case investigations' },
  { id: 'CRIME_ANALYST', label: 'Crime Analyst', description: 'Analyse patterns and trends' },
]

export function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')

  const steps = [
    { title: 'Welcome to ANVAYA', content: <div><p className="text-sm text-slate-600">Let's get you started. Enter your name to personalise the experience.</p><input type="text" value={name} onChange={e => setName(e.target.value)} className="mt-4 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Your name" /></div> },
    { title: 'What brings you here?', content: <div className="space-y-3">{roles.map(role => <button key={role.id} type="button" onClick={() => { navigate('/dashboard', { replace: true }) }} className="w-full rounded-lg border border-slate-200 p-4 text-left transition hover:border-teal-400"><p className="font-medium text-navy-950">{role.label}</p><p className="text-xs text-slate-500">{role.description}</p></button>)}</div> },
    { title: 'You\'re all set!', content: <div><p className="text-sm text-slate-600">Redirecting to the dashboard...</p></div> },
  ]

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6">
          <div className="flex gap-1">
            {steps.map((_, i) => <div key={i} className={`h-1 flex-1 rounded-full ${i <= step ? 'bg-teal-500' : 'bg-slate-200'}`} />)}
          </div>
          <h1 className="mt-6 text-xl font-bold text-navy-950">{steps[step].title}</h1>
        </div>
        {steps[step].content}
        <div className="mt-6 flex justify-between">
          {step > 0 && <button type="button" onClick={() => setStep(s => s - 1)} className="text-sm text-slate-500 hover:text-slate-700">Back</button>}
          {step < steps.length - 1 ? (
            <button type="button" onClick={() => setStep(s => s + 1)} className="ml-auto rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700">Continue</button>
          ) : (
            <button type="button" onClick={() => navigate('/dashboard', { replace: true })} className="ml-auto rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700">Go to Dashboard</button>
          )}
        </div>
      </div>
    </div>
  )
}
