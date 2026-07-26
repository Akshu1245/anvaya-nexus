import { ReportConsole } from '../features/m6/ReportConsole'

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-950">Reports</h1>
        <p className="mt-1 text-sm text-slate-500">Build and review investigation dossiers</p>
      </div>
      <ReportConsole />
    </div>
  )
}
