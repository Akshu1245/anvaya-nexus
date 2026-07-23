import {useEffect,useRef} from 'react'

const label=(key:string)=>key.replaceAll('_',' ').replace(/\b\w/g,letter=>letter.toUpperCase())

export function SourcePassportDrawer({passport,onClose}:{passport:any;onClose:()=>void}){
 const closeRef=useRef<HTMLButtonElement>(null)
 const panelRef=useRef<HTMLElement>(null)
 useEffect(()=>{
  const previous=document.activeElement as HTMLElement|null
  closeRef.current?.focus()
  const onKey=(event:KeyboardEvent)=>{
   if(event.key==='Escape'){onClose();return}
   if(event.key!=='Tab'||!panelRef.current)return
   const focusable=Array.from(panelRef.current.querySelectorAll<HTMLElement>('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')).filter(node=>!node.hasAttribute('disabled'))
   if(!focusable.length)return
   const first=focusable[0],last=focusable[focusable.length-1]
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
  }
  window.addEventListener('keydown',onKey)
  return()=>{window.removeEventListener('keydown',onKey);previous?.focus?.()}
 },[onClose])
 const entries=Object.entries(passport||{}).filter(([,value])=>typeof value!=='object'||value===null)
 return <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/45 p-3" role="presentation" onMouseDown={onClose}>
  <aside ref={panelRef} className="h-full w-full max-w-xl animate-slide-in-right overflow-y-auto rounded-2xl border-t-4 border-teal-400 bg-white p-6 shadow-2xl" role="dialog" aria-modal="true" aria-label="Source Passport" onMouseDown={event=>event.stopPropagation()}>
   <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-teal-700">Provenance</p><h3 className="mt-1 text-xl font-semibold">Source Passport</h3><p className="mt-1 text-sm text-slate-600">This explains the source, permitted use and known limitations behind the selected record.</p></div><button ref={closeRef} className="rounded border px-3 py-2 text-sm" onClick={onClose}>Close</button></div>
   <dl className="mt-6 grid gap-3">{entries.length===0?<p className="text-sm text-slate-500">No source passport fields are available.</p>:entries.map(([key,value])=><div className="rounded-xl border border-slate-200 bg-slate-50 p-3" key={key}><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label(key)}</dt><dd className="mt-1 break-words text-sm text-slate-900">{String(value||'Not recorded')}</dd></div>)}</dl>
   {(passport?.transformation_history||passport?.transformations)?.length>0&&<section className="mt-6"><h4 className="font-semibold">Transformation history</h4><ul className="mt-2 space-y-2 text-sm">{(passport.transformation_history||passport.transformations).map((item:any,index:number)=><li className="rounded border p-3" key={index}>{item.operation||'Recorded transformation'}{item.source_field&&<>: {item.source_field} → {item.target_field}</>} {item.outcome&&<>· {item.outcome}</>}</li>)}</ul></section>}
  </aside>
 </div>
}
