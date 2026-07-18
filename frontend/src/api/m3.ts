export type User={id:string;username:string;role:'INVESTIGATOR'|'CRIME_ANALYST'|'SUPERVISOR';assigned_station:string|null;assigned_district:string|null}
export type Source={id:string;name:string;status:string;selectable:boolean}
export type Investigation={id:string;title:string;purpose:string;selected_sources:string[];assigned_station:string|null;assigned_district:string|null}
type Envelope<T>={data:T;warnings:string[];request_id:string}
async function call<T>(url:string,options?:RequestInit):Promise<T>{const r=await fetch(url,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options?.headers||{})},...options});const b=await r.json();if(!r.ok)throw new Error(b.message||'Request failed.');return (b as Envelope<T>).data}
export const m3Api={
 login:(username:string,password:string)=>call<User>('/api/auth/login',{method:'POST',body:JSON.stringify({username,password})}),
 session:()=>call<User>('/api/auth/session'),
 logout:()=>call<{logged_out:boolean}>('/api/auth/logout',{method:'POST'}),
 sources:()=>call<Source[]>('/api/m3/sources'),
 home:()=>call<any>('/api/investigation-home'),
 sourceControl:(purpose:string)=>call<any>(`/api/source-control?purpose=${encodeURIComponent(purpose)}`),
 createInvestigation:(payload:object)=>call<Investigation>('/api/investigations',{method:'POST',body:JSON.stringify(payload)}),
 investigations:()=>call<Investigation[]>('/api/investigations'),
 updateSources:(id:string,selected_sources:string[])=>call<Investigation>(`/api/investigations/${id}/sources`,{method:'PATCH',body:JSON.stringify({selected_sources})}),
 preset:(id:string,preset:string)=>call<Investigation>(`/api/investigations/${id}/sources/preset`,{method:'POST',body:JSON.stringify({preset})}),
 history:(id:string)=>call<any[]>(`/api/investigations/${id}/history`),
 preview:(id:string,query:string)=>call<any>(`/api/investigations/${id}/query/preview`,{method:'POST',body:JSON.stringify({query})}),
 followUp:(id:string,parent_message_id:string,query:string)=>call<any>(`/api/investigations/${id}/query/follow-up`,{method:'POST',body:JSON.stringify({parent_message_id,query})}),
 validate:(plan:object)=>call<any>('/api/query/validate',{method:'POST',body:JSON.stringify(plan)}),
 search:(id:string,plan:object)=>call<any>(`/api/investigations/${id}/search`,{method:'POST',body:JSON.stringify(plan)}),
 discover:(id:string,plan:object)=>call<any>(`/api/investigations/${id}/discover`,{method:'POST',body:JSON.stringify(plan)}),
 case360:(id:string)=>call<any>(`/api/cases/${id}/360`),
 passport:(id:string)=>call<any>(`/api/source-passports/${id}`),
 path:(from:string,to:string)=>call<any>(`/api/relationships/path?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`),
 dna:(left:string,right:string)=>call<any>(`/api/m5/case-dna/${left}/${right}`), graph:(id:string)=>call<any>(`/api/m5/graph/${id}`), assurance:(id:string)=>call<any>(`/api/m5/assurance/${id}`), verify:(left:string,right:string)=>call<any>(`/api/m5/verify/${left}/${right}`), challenge:(id:string,hypothesis:string)=>call<any>(`/api/m5/challenge/${id}`,{method:'POST',body:JSON.stringify({hypothesis})}), actions:(id:string)=>call<any>(`/api/m5/actions/${id}`),
 createReport:(payload:object)=>call<any>('/api/reports',{method:'POST',body:JSON.stringify(payload)}), updateReport:(id:string,payload:object)=>call<any>(`/api/reports/${id}`,{method:'PATCH',body:JSON.stringify(payload)}), submitReport:(id:string)=>call<any>(`/api/reports/${id}/submit`,{method:'POST'}), reportPreview:(id:string)=>call<any>(`/api/reports/${id}/preview`), reviewReport:(id:string,payload:object)=>call<any>(`/api/reports/${id}/review`,{method:'POST',body:JSON.stringify(payload)}), newReportVersion:(id:string)=>call<any>(`/api/reports/${id}/versions`,{method:'POST'}), audit:(params:string)=>call<any>(`/api/audit-events?${params}`), systemHealth:()=>call<any>('/api/system-health'),
 reports:()=>call<any>('/api/reports'), reviewers:()=>call<any[]>('/api/reviewers'), assignReviewer:(id:string,reviewer:string)=>call<any>(`/api/reports/${id}/assign`,{method:'POST',body:JSON.stringify({reviewer})}), reportDetail:(id:string)=>call<any>(`/api/reports/${id}`), previewMetadata:(id:string)=>call<any>(`/api/reports/${id}/preview-metadata`),
}
