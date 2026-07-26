import { useState } from 'react'
import { useAuthStore } from '../../stores/authStore'
import { useLocale } from '../../i18n/portal'

type EvidenceItem = {
  id: string
  type: 'document' | 'exhibit' | 'forensic' | 'digital' | 'photo'
  name: string
  caseId: string
  date: string
  status: 'pending' | 'verified' | 'chain_of_custody'
  source: string
}

const SAMPLE_EVIDENCE: EvidenceItem[] = [
  { id: 'EV-001', type: 'document', name: 'First Information Report — SYN-FIR-1034', caseId: 'SYN-FIR-1034', date: '2025-11-14', status: 'verified', source: 'Jayanagar PS' },
  { id: 'EV-002', type: 'digital', name: 'CCTV Footage Timestamp Log', caseId: 'SYN-FIR-1034', date: '2025-11-14', status: 'chain_of_custody', source: 'Digital Forensics Unit' },
  { id: 'EV-003', type: 'forensic', name: 'Fingerprint Analysis Report', caseId: 'SYN-FIR-1021', date: '2025-10-08', status: 'verified', source: 'FSL Bengaluru' },
  { id: 'EV-004', type: 'exhibit', name: 'Recovered Vehicle — KA-05-MF-4421', caseId: 'SYN-FIR-1089', date: '2025-12-01', status: 'chain_of_custody', source: 'Traffic Unit' },
  { id: 'EV-005', type: 'photo', name: 'Crime Scene Photography — Set A', caseId: 'SYN-FIR-1067', date: '2025-11-28', status: 'verified', source: 'Photography Cell' },
  { id: 'EV-006', type: 'document', name: 'Witness Statement — Person SYN-PER-0412', caseId: 'SYN-FIR-1067', date: '2025-11-30', status: 'pending', source: 'Investigating Officer' },
  { id: 'EV-007', type: 'digital', name: 'Mobile Device Extraction Report', caseId: 'SYN-FIR-1021', date: '2025-10-10', status: 'verified', source: 'Cyber Crime Cell' },
  { id: 'EV-008', type: 'forensic', name: 'DNA Sample Analysis', caseId: 'SYN-FIR-1034', date: '2025-11-20', status: 'pending', source: 'FSL Mysuru' },
]

const TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string; label: string }> = {
  document: { icon: 'description', color: '#2563eb', bg: '#eff6ff', label: 'Document' },
  exhibit: { icon: 'inventory_2', color: '#7c3aed', bg: '#f5f3ff', label: 'Physical Exhibit' },
  forensic: { icon: 'biotech', color: '#059669', bg: '#ecfdf5', label: 'Forensic Report' },
  digital: { icon: 'computer', color: '#d97706', bg: '#fffbeb', label: 'Digital Evidence' },
  photo: { icon: 'photo_camera', color: '#db2777', bg: '#fdf2f8', label: 'Photography' },
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  pending: { label: 'Pending Verification', color: '#d97706', bg: '#fffbeb', icon: 'pending' },
  verified: { label: 'Verified', color: '#059669', bg: '#ecfdf5', icon: 'verified' },
  chain_of_custody: { label: 'Chain of Custody', color: '#2563eb', bg: '#eff6ff', icon: 'link' },
}

export function EvidenceView() {
  const user = useAuthStore((s) => s.user)
  const { t } = useLocale()
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [previewItem, setPreviewItem] = useState<EvidenceItem | null>(null)

  const downloadEvidence = (item: EvidenceItem) => {
    const fileContent = `================================================================================
 KARNATAKA STATE POLICE — EVIDENCE REPOSITORY CERTIFICATE
 Reference ID: ${item.id}
 Classification: ${(TYPE_CONFIG[item.type]?.label || item.type).toUpperCase()}
 Status: ${item.status.toUpperCase()}
 ================================================================================

 EVIDENCE RECORD DETAILS:
 -------------------------
 Title / Name        : ${item.name}
 FIR / Case Reference: ${item.caseId}
 Source Department   : ${item.source}
 Registration Date   : ${item.date}

 CHAIN OF CUSTODY & VERIFICATION AUDIT:
 ---------------------------------------
 Custody Location    : KSP Evidence Vault (${item.source})
 Audit Hash SHA256   : 9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a
 Verification        : ${item.status === 'verified' ? 'DIGITALLY VERIFIED ✓ (Tamper-proof digital seal active)' : 'LOGGED IN CHAIN OF CUSTODY'}
 Officer Assigned    : Investigating Officer (ANVAYA ID: KSP-INV-2026)

 PROVENANCE STATEMENT:
 ---------------------
 This evidence item is officially catalogued under the Karnataka State Police (KSP) 
 Digital & Physical Evidence Management Repository for FIR ${item.caseId}.

 DISCLAIMER & NOTICE:
 -------------------
 Synthetic Data: All evidence records shown are generated for the KSP Datathon 2026 prototype.
 This is not a live evidence management system. No real case data is stored or processed.
 ================================================================================`

    const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.id}_${item.caseId}_Evidence_Report.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const filtered = SAMPLE_EVIDENCE.filter((e) => {
    const matchType = filter === 'all' || e.type === filter
    const matchSearch = !search ||
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.caseId.toLowerCase().includes(search.toLowerCase())
    return matchType && matchSearch
  })

  const counts = {
    all: SAMPLE_EVIDENCE.length,
    document: SAMPLE_EVIDENCE.filter((e) => e.type === 'document').length,
    exhibit: SAMPLE_EVIDENCE.filter((e) => e.type === 'exhibit').length,
    forensic: SAMPLE_EVIDENCE.filter((e) => e.type === 'forensic').length,
    digital: SAMPLE_EVIDENCE.filter((e) => e.type === 'digital').length,
    photo: SAMPLE_EVIDENCE.filter((e) => e.type === 'photo').length,
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6" style={{ fontFamily: "'Inter', sans-serif" }}>
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="material-icons-outlined" style={{ fontSize: 22, color: '#003087' }}>inventory_2</span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">{t('evidence.title')}</h2>
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {t('evidence.subtitle')}
              {user?.assigned_station ? ` · ${user.assigned_station}` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold"
              style={{ background: '#fff7ed', border: '1px solid #fed7aa', color: '#92400e' }}>
              <span className="material-icons-outlined" style={{ fontSize: 13 }}>science</span>
              Synthetic Data Only
            </span>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Total Evidence', value: SAMPLE_EVIDENCE.length, icon: 'folder_open', color: '#003087' },
            { label: 'Verified', value: SAMPLE_EVIDENCE.filter((e) => e.status === 'verified').length, icon: 'verified', color: '#059669' },
            { label: 'Pending', value: SAMPLE_EVIDENCE.filter((e) => e.status === 'pending').length, icon: 'pending', color: '#d97706' },
            { label: 'In Custody', value: SAMPLE_EVIDENCE.filter((e) => e.status === 'chain_of_custody').length, icon: 'link', color: '#7c3aed' },
          ].map((s) => (
            <div key={s.label} className="rounded-xl bg-white p-4 shadow-sm dark:bg-[#161b26]" style={{ border: '1px solid #e2e8f0' }}>
              <div className="flex items-center gap-2">
                <span className="material-icons-outlined" style={{ fontSize: 20, color: s.color }}>{s.icon}</span>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{s.label}</p>
                  <p className="text-xl font-bold" style={{ color: s.color }}>{s.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Filters + Search */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-48">
            <span className="material-icons-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" style={{ fontSize: 18 }}>search</span>
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search evidence or case ID…"
              className="w-full rounded-lg pl-9 pr-4 py-2.5 text-sm outline-none text-slate-800 dark:text-white dark:bg-slate-800"
              style={{ border: '1.5px solid #d0d9e8' }}
              onFocus={(e) => e.target.style.borderColor = '#003087'}
              onBlur={(e) => e.target.style.borderColor = '#d0d9e8'} />
          </div>

          {/* Type filters */}
          <div className="flex flex-wrap gap-1.5">
            {(['all', 'document', 'exhibit', 'forensic', 'digital', 'photo'] as const).map((t) => (
              <button key={t} onClick={() => setFilter(t)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all capitalize"
                style={{
                  background: filter === t ? '#003087' : '#fff',
                  color: filter === t ? '#fff' : '#64748b',
                  border: filter === t ? '1.5px solid #003087' : '1.5px solid #e2e8f0',
                }}>
                {t !== 'all' && <span className="material-icons-outlined" style={{ fontSize: 13 }}>{TYPE_CONFIG[t]?.icon}</span>}
                {t === 'all' ? `All (${counts.all})` : `${TYPE_CONFIG[t]?.label} (${counts[t]})`}
              </button>
            ))}
          </div>
        </div>

        {/* Evidence list */}
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="rounded-xl bg-white p-10 text-center" style={{ border: '1px dashed #d0d9e8' }}>
              <span className="material-icons-outlined text-4xl text-slate-300">search_off</span>
              <p className="mt-2 text-sm text-slate-500">No evidence matching your filters.</p>
            </div>
          ) : (
            filtered.map((item) => {
              const typeConf = TYPE_CONFIG[item.type]
              const statusConf = STATUS_CONFIG[item.status]
              return (
                <div key={item.id} className="rounded-xl bg-white p-4 flex items-start gap-4 transition-all dark:bg-[#161b26] dark:border-slate-800"
                  style={{ border: '1px solid #e2e8f0', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,48,135,0.1)')}
                  onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.04)')}>

                  {/* Type icon */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                    style={{ background: typeConf.bg }}>
                    <span className="material-icons-outlined" style={{ fontSize: 20, color: typeConf.color }}>{typeConf.icon}</span>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-semibold text-slate-900 text-sm truncate dark:text-white">{item.name}</p>
                      <span className="flex shrink-0 items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold"
                        style={{ background: statusConf.bg, color: statusConf.color }}>
                        <span className="material-icons-outlined" style={{ fontSize: 11 }}>{statusConf.icon}</span>
                        {statusConf.label}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <span className="material-icons-outlined" style={{ fontSize: 12 }}>folder</span>
                        {item.caseId}
                      </span>
                      <span className="text-slate-300">·</span>
                      <span className="flex items-center gap-1">
                        <span className="material-icons-outlined" style={{ fontSize: 12 }}>location_city</span>
                        {item.source}
                      </span>
                      <span className="text-slate-300">·</span>
                      <span className="flex items-center gap-1">
                        <span className="material-icons-outlined" style={{ fontSize: 12 }}>calendar_today</span>
                        {item.date}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold"
                        style={{ background: typeConf.bg, color: typeConf.color }}>
                        {typeConf.label}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="shrink-0 flex items-center gap-2">
                    <button
                      onClick={() => setPreviewItem(item)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border border-slate-300 text-slate-700 bg-slate-50 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                      title="View Details">
                      <span className="material-icons-outlined" style={{ fontSize: 16 }}>visibility</span>
                      Preview
                    </button>
                    <button
                      onClick={() => downloadEvidence(item)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border border-teal-600 bg-teal-600 text-white hover:bg-teal-700 shadow-sm"
                      title="Download Official Evidence Certificate">
                      <span className="material-icons-outlined" style={{ fontSize: 16 }}>download</span>
                      Download
                    </button>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Synthetic data note */}
        <div className="mt-6 rounded-xl px-4 py-3 flex items-start gap-2"
          style={{ background: '#fff7ed', border: '1px solid #fed7aa' }}>
          <span className="material-icons-outlined shrink-0 text-amber-600" style={{ fontSize: 16 }}>warning_amber</span>
          <p className="text-xs text-amber-700">
            <strong>Synthetic Data:</strong> All evidence records shown are generated for the KSP Datathon 2026 prototype.
            This is not a live evidence management system. No real case data is stored or processed.
          </p>
        </div>

        {/* Preview Modal */}
        {previewItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
            <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-[#161b26] dark:text-white">
              <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ background: TYPE_CONFIG[previewItem.type]?.bg }}>
                    <span className="material-icons-outlined" style={{ fontSize: 22, color: TYPE_CONFIG[previewItem.type]?.color }}>
                      {TYPE_CONFIG[previewItem.type]?.icon}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base dark:text-white">{previewItem.name}</h3>
                    <p className="text-xs text-slate-500">{previewItem.id} &middot; {previewItem.caseId}</p>
                  </div>
                </div>
                <button onClick={() => setPreviewItem(null)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800">
                  ✕
                </button>
              </div>

              <div className="mt-4 space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-3.5 dark:bg-slate-800/60">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Classification</span>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">{TYPE_CONFIG[previewItem.type]?.label}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Status</span>
                    <p className="font-semibold" style={{ color: STATUS_CONFIG[previewItem.status]?.color }}>
                      {STATUS_CONFIG[previewItem.status]?.label}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Source Unit</span>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">{previewItem.source}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Date Logged</span>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">{previewItem.date}</p>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-200 p-3 text-xs dark:border-slate-700">
                  <p className="font-bold text-slate-700 dark:text-slate-300">Security & Custody Verification</p>
                  <p className="mt-1 font-mono text-[11px] text-slate-500">SHA256: 9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a</p>
                  <p className="mt-1 text-slate-600 dark:text-slate-400">Location: KSP Secure Evidence Vault ({previewItem.source})</p>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button onClick={() => setPreviewItem(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300">
                  Close
                </button>
                <button
                  onClick={() => {
                    downloadEvidence(previewItem)
                    setPreviewItem(null)
                  }}
                  className="flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-700"
                >
                  <span className="material-icons-outlined" style={{ fontSize: 16 }}>download</span>
                  Download Certificate
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
