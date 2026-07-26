const OFFENCE_META: Record<string,{label:string;labelKn:string;src:string;tone:string}>={
  CHAIN_SNATCHING:{label:'Chain snatching',labelKn:'ಸರಗಳ್ಳತನ',src:'/offence-icons/chain-snatching.svg',tone:'bg-teal-50 ring-teal-200 text-teal-900'},
  HOUSEBREAKING:{label:'Housebreaking',labelKn:'ಮನೆಕಳ್ಳತನ',src:'/offence-icons/housebreaking.svg',tone:'bg-sky-50 ring-sky-200 text-sky-900'},
  VEHICLE_THEFT:{label:'Vehicle theft',labelKn:'ವಾಹನ ಕಳ್ಳತನ',src:'/offence-icons/vehicle-theft.svg',tone:'bg-emerald-50 ring-emerald-200 text-emerald-900'},
  ROBBERY:{label:'Robbery',labelKn:'ದರೋಡೆ',src:'/offence-icons/robbery.svg',tone:'bg-amber-50 ring-amber-200 text-amber-950'},
}

export function resolveOffenceKey(value?:string|null){
  if(!value)return null
  const upper=value.toUpperCase().replace(/\s+/g,'_')
  if(OFFENCE_META[upper])return upper
  if(upper.includes('CHAIN'))return 'CHAIN_SNATCHING'
  if(upper.includes('HOUSE')||upper.includes('BURGL'))return 'HOUSEBREAKING'
  if(upper.includes('VEHICLE')||upper.includes('AUTO'))return 'VEHICLE_THEFT'
  if(upper.includes('ROBB'))return 'ROBBERY'
  return null
}

export function OffenceVisual({offence,compact=false}:{offence?:string|null;compact?:boolean}){
  const key=resolveOffenceKey(offence)
  const meta=key?OFFENCE_META[key]:null
  if(!meta){
    return <div className={`flex items-center justify-center rounded-xl bg-slate-100 ring-1 ring-slate-200 ${compact?'h-12 w-16':'h-20 w-full'}`} aria-hidden>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h7l2 2h9v10H3z"/></svg>
    </div>
  }
  return <figure className={`overflow-hidden rounded-xl ring-1 ring-black/5 ${compact?'h-12 w-16':'w-full'}`}>
    <img src={meta.src} alt={`${meta.label} case illustration`} className={`h-full w-full object-cover ${compact?'':'aspect-[4/3]'}`} loading="lazy"/>
  </figure>
}

export function OffenceBadge({offence}:{offence?:string|null}){
  const key=resolveOffenceKey(offence)
  const meta=key?OFFENCE_META[key]:null
  if(!meta)return null
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ${meta.tone}`}>{meta.label}</span>
}

export const OFFENCE_CATALOGUE=Object.entries(OFFENCE_META).map(([code,meta])=>({code,label:meta.label,labelKn:meta.labelKn,src:meta.src}))
