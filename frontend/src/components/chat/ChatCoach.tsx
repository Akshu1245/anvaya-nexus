const coachSteps = [
  { title: 'Ask in the composer', text: 'Use English, ಕನ್ನಡ, हिन्दी or code-mixed phrases in the composer.' },
  { title: 'Try an example', text: 'Example chips show useful synthetic searches and shortcuts.' },
  { title: 'Confirm before search', text: 'ANVAYA never runs an interpreted record search until you click Search records.' },
  { title: 'Open Case 360', text: 'Inspect a result in-thread and check its source passports.' },
  { title: 'Export a dossier', text: 'Ask "send me PDF" after opening a case, or export the chat from Help.' },
]

type ChatCoachProps = {
  step: number
  onNext: () => void
  onDismiss: () => void
}

export function ChatCoach({ step, onNext, onDismiss }: ChatCoachProps) {
  if (step < 0 || step >= coachSteps.length) return null

  const current = coachSteps[step]
  const isLast = step === coachSteps.length - 1

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-blue-950/55 p-5">
      <section
        role="dialog"
        aria-modal="true"
        aria-label="ANVAYA first-run coach"
        className="relative w-full max-w-md rounded-2xl border-2 border-blue-300 bg-white p-6 shadow-2xl ring-8 ring-blue-400/30"
      >
        <span className="text-xs font-bold uppercase tracking-widest text-blue-700">
          Step {step + 1} of {coachSteps.length}
        </span>
        <h3 className="mt-2 text-xl font-semibold text-navy-950">{current.title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-600">{current.text}</p>
        <div className="mt-5 flex items-center justify-between">
          <button type="button" onClick={onDismiss} className="text-sm font-semibold text-slate-500 hover:text-slate-800">
            Skip
          </button>
          <button
            type="button"
            onClick={onNext}
            className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-bold text-white hover:bg-blue-800"
          >
            {isLast ? 'Finish' : 'Next'}
          </button>
        </div>
      </section>
    </div>
  )
}
