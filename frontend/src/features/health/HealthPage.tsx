import { useQuery } from '@tanstack/react-query'

import { fetchHealth } from '../../api/health'
import { useFoundationStore } from '../../stores/foundationStore'

export function HealthPage() {
  const recordCheck = useFoundationStore((state) => state.recordCheck)
  const lastCheckedAt = useFoundationStore((state) => state.lastCheckedAt)
  const query = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const result = await fetchHealth()
      recordCheck()
      return result
    },
  })

  return (
    <section aria-labelledby="health-title" className="max-w-3xl rounded-2xl border border-slate-200 bg-white p-7 shadow-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-500">Foundation status</p>
          <h2 id="health-title" className="mt-2 text-2xl font-semibold text-navy-950">Local service health</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Checks the Flask API and its local SQLite repository without any external service.</p>
        </div>
        <button
          type="button"
          onClick={() => void query.refetch()}
          disabled={query.isFetching}
          className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-semibold text-white hover:bg-navy-900 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Check again
        </button>
      </div>

      <div aria-live="polite" className="mt-7 rounded-xl border border-slate-200 bg-slate-50 p-5">
        {query.isPending && <p className="font-medium text-slate-700">Checking local services…</p>}
        {query.isError && (
          <div>
            <p className="font-semibold text-red-800">Health check failed</p>
            <p className="mt-1 text-sm text-red-700">{query.error.message}</p>
          </div>
        )}
        {query.isSuccess && (
          <div>
            <p className="font-semibold text-emerald-800">All local foundation services are healthy</p>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
              <div><dt className="text-slate-500">API</dt><dd className="font-medium">{query.data.data.service}</dd></div>
              <div><dt className="text-slate-500">Environment</dt><dd className="font-medium capitalize">{query.data.data.environment}</dd></div>
              <div><dt className="text-slate-500">SQLite</dt><dd className="font-medium uppercase">{query.data.data.database}</dd></div>
            </dl>
            {lastCheckedAt && <p className="mt-4 text-xs text-slate-500">Checked {new Date(lastCheckedAt).toLocaleTimeString()}</p>}
          </div>
        )}
      </div>
    </section>
  )
}
