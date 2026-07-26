import {useState} from 'react'
import {m3Api} from '../../api/m3'
import {btnOutline,btnSecondary} from '../../components/PortalButtons'

const DISCLAIMER='Shared record only — not identity, coordination, or guilt.'

function HubDiagram({data}:{data:any}){
 const graph=data?.graph||data||{}
 const nodes:any[]=graph.nodes||[]
 const edges:any[]=graph.edges||[]
 const baseId=graph.base_case_id||nodes[0]?.id
 const spokes=nodes.filter(node=>node.id!==baseId).slice(0,8)
 if(spokes.length===0)return <p className="mt-4 text-sm text-slate-500">No candidate connections to draw for this response. Any relationships remain shared records only — never identity, guilt or risk.</p>
 return <div className="mt-4">
  <svg role="img" aria-label="Candidate shared-record network" viewBox="0 0 600 220" className="h-56 w-full rounded-xl border border-slate-200 bg-slate-50">
   {spokes.map((node,index)=>{const angle=index*Math.PI*2/spokes.length,x=300+230*Math.cos(angle),y=110+80*Math.sin(angle);return <line key={`l-${node.id||index}`} x1="300" y1="110" x2={x} y2={y} stroke="#b0e9e5" strokeWidth="1.5"/>})}
   {spokes.map((node,index)=>{const angle=index*Math.PI*2/spokes.length,x=300+230*Math.cos(angle),y=110+80*Math.sin(angle);return <g key={`n-${node.id||index}`}><circle cx={x} cy={y} r="22" fill="#d6f5f2" stroke="#177474" strokeWidth="1.5"/><text x={x} y={y+4} textAnchor="middle" fontSize="9" fill="#123e3e">{String(node.type||node.label||'NODE').slice(0,10)}</text></g>})}
   <circle cx="300" cy="110" r="38" fill="#0d1b2a"/>
   <text x="300" y="106" textAnchor="middle" fontSize="11" fontWeight="700" fill="#eefbfa">Base FIR</text>
   <text x="300" y="120" textAnchor="middle" fontSize="8" fill="#70c5c5">{String(baseId||'').slice(0,12)}</text>
  </svg>
  {edges.length>0&&<ul className="mt-3 space-y-1 text-xs text-slate-600">{edges.slice(0,10).map((edge:any,index:number)=><li key={edge.id||index} className="rounded border border-slate-200 bg-white px-2 py-1"><b className="text-navy-900">{String(edge.relationship_type||edge.type||'shared record').replaceAll('_',' ')}</b>{edge.factual_basis?<span className="ml-2">{edge.factual_basis}</span>:null}</li>)}</ul>}
 </div>
}

export function IntelligencePanel({caseId='SYN-CASE-0001',purpose='Active Case Investigation'}:{caseId?:string;purpose?:string}){
 const [data,setData]=useState<any>(null)
 const [kind,setKind]=useState('')
 const [hypothesis,setHypothesis]=useState('These cases may involve the same operational group.')
 const run=async(k:string)=>{
  setKind(k)
  if(k==='dna')setData(await m3Api.dna(caseId,'SYN-CASE-0002',purpose))
  if(k==='graph')setData(await m3Api.graph(caseId,purpose))
  if(k==='assurance')setData(await m3Api.assurance(caseId,purpose))
  if(k==='verify')setData(await m3Api.verify(caseId,'SYN-CASE-0002',purpose))
  if(k==='actions')setData(await m3Api.actions(caseId,purpose))
  if(k==='challenge')setData(await m3Api.challenge(caseId,hypothesis,purpose))
 }
 return <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" aria-label="M5 Intelligence Panel">
  <div className="flex flex-wrap items-start justify-between gap-3">
   <div>
    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-teal-700">Candidate support only</p>
    <h3 className="mt-1 text-lg font-semibold text-navy-950">M5 Intelligence</h3>
    <p className="mt-1 text-sm text-slate-600">Similarity is never identity, guilt, risk, or an automatic action.</p>
   </div>
   <span className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800">{DISCLAIMER}</span>
  </div>
  <div className="mt-4 flex flex-wrap gap-2">{['dna','graph','assurance','verify','actions'].map(x=><button key={x} type="button" className={`${btnOutline} !px-3 !py-1.5 !text-xs uppercase tracking-wide ${kind===x?'!border-teal-600 !bg-teal-50 !text-teal-800':''}`} onClick={()=>void run(x)}>{x}</button>)}</div>
  <div className="mt-4 flex flex-wrap items-end gap-2">
   <label className="flex-1 text-sm font-medium text-slate-600">Hypothesis
    <input aria-label="Hypothesis" className="mt-1 w-full rounded-lg border border-slate-200 p-2 focus:ring-2 focus:ring-teal-300" value={hypothesis} onChange={e=>setHypothesis(e.target.value)}/>
   </label>
   <button type="button" className={btnSecondary} onClick={()=>void run('challenge')}>Challenge hypothesis</button>
  </div>
  {kind==='actions'&&<p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Preview only — no action is executed.</p>}
  {kind==='graph'&&data&&<HubDiagram data={data}/>}
  {data&&<details className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3"><summary className="cursor-pointer text-sm font-medium text-slate-700">Raw response ({kind||'result'})</summary><pre className="mt-2 max-h-72 overflow-auto text-xs text-slate-700">{JSON.stringify(data,null,2)}</pre></details>}
 </section>
}
