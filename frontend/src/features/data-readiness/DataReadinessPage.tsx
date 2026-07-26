import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { commitImport, listSources, type ImportJob, validateFile } from '../../api/dataReadiness'

export function DataReadinessPage(){
  const [file,setFile]=useState<File|null>(null);const [job,setJob]=useState<ImportJob|null>(null);const [error,setError]=useState('');const [validating,setValidating]=useState(false);const [committing,setCommitting]=useState(false)
  const sources=useQuery({queryKey:['sources'],queryFn:listSources})
  async function validate(){if(!file)return;setError('');setValidating(true);try{setJob(await validateFile(file))}catch(e){setError(e instanceof Error?e.message:'Validation failed.')}finally{setValidating(false)}}
  async function commit(){if(!job)return;setError('');setCommitting(true);try{setJob(await commitImport(job.id))}catch(e){setError(e instanceof Error?e.message:'Commit failed.')}finally{setCommitting(false)}}
  return <section aria-labelledby="readiness-title" className="mt-8 rounded-2xl border border-slate-200 bg-white p-7 shadow-panel">
    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-500">M2 synthetic import</p><h2 id="readiness-title" className="mt-2 text-2xl font-semibold">Data Readiness</h2>
    <p className="mt-2 text-sm text-slate-600">Validate a synthetic CCTNS-style CSV or JSON file before accepted rows enter the canonical store.</p>
    <div className="mt-5 flex flex-wrap gap-3"><input aria-label="Synthetic CSV or JSON file" type="file" accept=".csv,.json" onChange={e=>setFile(e.target.files?.[0]??null)}/><button className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={!file||validating} onClick={()=>void validate()}>{validating?'Validating…':'Validate'}</button></div>
    {file&&<p className="mt-2 text-xs text-slate-500">Selected: {file.name}</p>}{error&&<p role="alert" className="mt-4 text-sm font-semibold text-red-700">{error}</p>}
    <div className="mt-6"><h3 className="font-semibold">Source status</h3><div className="mt-2 flex flex-wrap gap-2">{sources.isLoading&&<span>Loading sources…</span>}{sources.isError&&<span className="text-red-700">Source registry unavailable</span>}{sources.data?.map(source=><span key={source.id} className="rounded-full border px-3 py-1 text-xs"><strong>{source.status}</strong> · {source.name}</span>)}</div></div>
    {job&&<div className="mt-7 border-t pt-6"><div className="grid gap-3 sm:grid-cols-4"><Summary label="Status" value={job.status}/><Summary label="Accepted" value={String(job.accepted_count)}/><Summary label="Failed" value={String(job.failed_count)}/><Summary label="Version" value={job.source_version}/></div>
      <p className="mt-4 break-all text-xs text-slate-500">Checksum: {job.checksum}</p><p className="mt-2 text-sm"><strong>Mapped fields:</strong> {job.mapped_fields.join(', ')||'None'}</p>
      {job.failures.length>0&&<table className="mt-4 w-full text-left text-sm"><thead><tr><th>Row</th><th>Category</th><th>Reason</th></tr></thead><tbody>{job.failures.map((f,i)=><tr key={`${f.row}-${i}`}><td>{f.row}</td><td>{f.category}</td><td>{f.reason}</td></tr>)}</tbody></table>}
      <button className="mt-5 rounded-lg bg-teal-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={job.accepted_count===0||Boolean(job.committed_at)||committing} onClick={()=>void commit()}>{committing?'Committing…':job.committed_at?'Accepted rows committed':'Commit accepted rows'}</button>
    </div>}
  </section>
}
function Summary({label,value}:{label:string;value:string}){return <div className="rounded-lg bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="font-semibold">{value}</p></div>}
