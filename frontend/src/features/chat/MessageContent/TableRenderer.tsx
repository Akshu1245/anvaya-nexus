type Column = { key: string; label: string }
type Props = {
  columns: Column[]
  rows: Record<string, any>[]
  onRowClick?: (row: Record<string, any>) => void
}

export function TableRenderer({ columns, rows, onRowClick }: Props) {
  if (!columns.length || !rows.length) return null

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-800">
            {columns.map((col) => (
              <th key={col.key} className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-700 dark:border-slate-600 dark:text-slate-300">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800 ${onRowClick ? 'cursor-pointer' : ''}`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-3 py-2 text-slate-600 dark:text-slate-400">
                  {String(row[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
