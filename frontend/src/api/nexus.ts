type Envelope<T>={data:T;warnings:string[];request_id:string}
async function call<T>(url:string,options?:RequestInit):Promise<T>{
 const response=await fetch(url,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options?.headers||{})},...options})
 const body=await response.json(); if(!response.ok) throw new Error(body.message||'Request failed.')
 return (body as Envelope<T>).data
}
export const nexusApi={
 search:(params:Record<string,string>)=>call<any>(`/api/fir/cases?${new URLSearchParams(Object.entries(params).filter(([,v])=>v))}`),
 case360:(id:string)=>call<any>(`/api/fir/cases/${id}/360`),
 brief:(id:string)=>call<any>(`/api/fir/cases/${id}/brief`),
 related:(id:string)=>call<any>(`/api/fir/cases/${id}/related-cases`),
 identities:(id:string)=>call<any>(`/api/fir/cases/${id}/identity-suggestions`),
 reviewIdentity:(id:string,payload:object)=>call<any>(`/api/fir/cases/${id}/identity-suggestions/review`,{method:'POST',body:JSON.stringify(payload)}),
 assurance:(id:string)=>call<any>(`/api/fir/cases/${id}/assurance`),
 graph:(id:string)=>call<any>(`/api/fir/cases/${id}/graph`),
 reportPreview:(id:string)=>call<any>(`/api/fir/cases/${id}/report-preview`),
 readiness:()=>call<any>('/api/fir/readiness'),
}
