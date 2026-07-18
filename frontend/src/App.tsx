import { NexusWorkspace } from './features/nexus/NexusWorkspace'

export function App() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <div
        role="note"
        className="bg-amber-100 px-4 py-2 text-center text-xs font-bold tracking-[0.12em] text-amber-950"
      >
        SYNTHETIC DATATHON PROTOTYPE — NOT FOR OPERATIONAL USE
      </div>
      <header className="border-b border-slate-700 bg-navy-950 text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-teal-300">ANVAYA NEXUS</p>
            <h1 className="mt-1 text-xl font-semibold">Explainable FIR Intelligence &amp; Investigation Assurance</h1>
          </div>
          <span className="rounded-full border border-slate-600 px-3 py-1 text-xs text-slate-300">Synthetic final demo</span>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-10">
        <NexusWorkspace />
      </main>
      <footer className="mx-auto max-w-6xl px-6 pb-8 text-xs text-slate-500">
        Every generated statement and derived relationship is accompanied by source references. This synthetic prototype must not be used for operational decisions.
      </footer>
    </div>
  )
}
