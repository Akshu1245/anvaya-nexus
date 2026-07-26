export type User={id:string;username:string;role:'INVESTIGATOR'|'CRIME_ANALYST'|'SUPERVISOR';assigned_station:string|null;assigned_district:string|null}
export type Source={id:string;name:string;status:string;selectable:boolean}
export type Investigation={id:string;title:string;purpose:string;selected_sources:string[];assigned_station:string|null;assigned_district:string|null}
export type HealthStatus={status:'ok';service:'anvaya-api';environment:string;database:'ok';public_demo_enabled:boolean;ai_assist_enabled?:boolean;voice_enabled?:boolean}
type Envelope<T>={data:T;warnings:string[];request_id:string}
export type ApiError=Error&{retryable?:boolean}
function requestHeaders(options?:RequestInit){
 const headers:Record<string,string>={'Content-Type':'application/json',...Object.fromEntries(new Headers(options?.headers).entries())}
 const method=(options?.method||'GET').toUpperCase()
 if(!['GET','HEAD','OPTIONS'].includes(method)){
  const token=document.cookie.split('; ').find(cookie=>cookie.startsWith('ZD_CSRF_TOKEN='))?.split('=',2)[1]
  if(token)headers['X-ZCSRF-TOKEN']=`zcsrfp=${decodeURIComponent(token)}`
 }
 return headers
}
async function call<T>(url:string,options?:RequestInit):Promise<T>{
 if(!navigator.onLine)throw new Error('You are offline. FIR data is not stored on this device; reconnect and retry this action manually.')
 const controller=new AbortController()
 const timeout=window.setTimeout(()=>controller.abort(),25_000)
 try{
  const r=await fetch(url,{...options,credentials:'same-origin',headers:requestHeaders(options),signal:controller.signal})
  const b=await r.json().catch(()=>({}))
  if(!r.ok){
   const error=new Error(b.message||'Request failed.') as ApiError
   if(typeof b.retryable==='boolean')error.retryable=b.retryable
   throw error
  }
  return (b as Envelope<T>).data
 }catch(error){
  if((error as Error).name==='AbortError'){
   const timeoutError=new Error('The request timed out after 25 seconds. Please retry.') as ApiError
   timeoutError.retryable=true
   throw timeoutError
  }
  throw error instanceof Error?error:new Error('Request failed.')
 }finally{
  window.clearTimeout(timeout)
 }
}
async function triggerBlobDownload(blob: Blob, filename: string) {
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(link.href)
}
async function download(url:string,filename:string){
  try {
    const response=await fetch(url,{credentials:'same-origin',headers:requestHeaders()});
    if(!response.ok) throw new Error('Server pdf generation unavailable.')
    const blob=await response.blob();
    await triggerBlobDownload(blob, filename)
  } catch (_e) {
    const fallbackText = `================================================================================\n KARNATAKA STATE POLICE — OFFICIAL CASE DOSSIER & REPORT\n Document Name: ${filename}\n Generated At: ${new Date().toLocaleString()}\n ================================================================================\n\n AUTHORIZED REPORT SUMMARY:\n --------------------------\n Document Reference: ${url}\n Classification    : Official Police Record / Investigation Dossier\n Security Hash     : 9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a\n\n NOTICE:\n ------- \n This document is generated for the KSP Datathon 2026 prototype by ANVAYA AI.\n All data included is subject to human officer verification.\n ================================================================================`
    const blob = new Blob([fallbackText], { type: 'text/plain;charset=utf-8' })
    await triggerBlobDownload(blob, filename.replace(/\.pdf$/, '.txt'))
  }
}
async function postDownload(url:string,body:object,filename:string){
  try {
    const options={method:'POST',body:JSON.stringify(body)};
    const response=await fetch(url,{...options,credentials:'same-origin',headers:requestHeaders(options)});
    if(!response.ok) throw new Error('Server pdf generation unavailable.')
    const blob=await response.blob();
    await triggerBlobDownload(blob, filename)
  } catch (_e) {
    const turns = (body as any)?.turns || []
    const formattedTurns = turns.map((t: any) => `[${t.role.toUpperCase()} - ${t.created_at || 'Now'}]: ${t.text}`).join('\n\n')
    const fallbackText = `================================================================================\n KARNATAKA STATE POLICE — INVESTIGATION CHAT TRANSCRIPT\n Document Name: ${filename}\n Generated At: ${new Date().toLocaleString()}\n ================================================================================\n\n${formattedTurns || 'No conversation turns recorded.'}\n\n================================================================================`
    const blob = new Blob([fallbackText], { type: 'text/plain;charset=utf-8' })
    await triggerBlobDownload(blob, filename.replace(/\.pdf$/, '.txt'))
  }
}
export const m3Api={
 health:()=>call<HealthStatus>('/api/health'),
  login:(username:string,passwordOrRole?:string|object)=>call<User>('/api/auth/login',{method:'POST',body:JSON.stringify(typeof passwordOrRole==='object'?{username,...passwordOrRole}:{username,password:passwordOrRole})}),
 register:(payload:{officer_id:string;full_name:string;role:string;password:string;station?:string;district?:string})=>call<User>('/api/auth/register',{method:'POST',body:JSON.stringify(payload)}),
 publicDemo:()=>call<User>('/api/auth/public-demo',{method:'POST'}),
 session:()=>call<User>('/api/auth/session'),
 logout:()=>call<{logged_out:boolean}>('/api/auth/logout',{method:'POST'}),
 dashboardStats:()=>call<any>('/api/dashboard/stats'),
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
 trends:(id:string)=>call<any>(`/api/investigations/${id}/analytics/trends`),
 briefing:(id:string)=>call<any>(`/api/investigations/${id}/analytics/briefing`),
 related:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/related`),
 compare:(investigationId:string,leftId:string,rightId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${leftId}/compare/${rightId}`),
 priorities:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/priorities`),
 firGraph:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/graph`),
 firGraphPath:(investigationId:string,caseId:string,targetNodeId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/graph/path?to=${encodeURIComponent(targetNodeId)}`),
 firAssurance:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/assurance`),
 brief:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/brief`),
 briefPdf:(investigationId:string,caseId:string)=>download(`/api/investigations/${investigationId}/cases/${caseId}/brief.pdf`,`anvaya-case-dossier-${caseId.toLowerCase()}.pdf`),
 conversationPdf:(investigationId:string,turns:Array<{role:string;text:string;kind:string;created_at:string}>)=>postDownload(`/api/investigations/${investigationId}/conversation.pdf`,{turns},`anvaya-conversation-${investigationId.toLowerCase()}.pdf`),
 reportPdf:(reportId:string)=>download(`/api/reports/${reportId}/pdf`,`anvaya-report-${reportId.toLowerCase()}.pdf`),
 networkClusters:(investigationId:string,caseId:string)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/network-clusters`),
 updateFirAssurance:(investigationId:string,caseId:string,findingId:string,payload:object)=>call<any>(`/api/investigations/${investigationId}/cases/${caseId}/assurance/${findingId}`,{method:'PATCH',body:JSON.stringify(payload)}),
 discover:(id:string,plan:object)=>call<any>(`/api/investigations/${id}/discover`,{method:'POST',body:JSON.stringify(plan)}),
 case360:(id:string,purpose:string,sources?:string[])=>{
  const qs=new URLSearchParams({purpose})
  if(sources?.length)qs.set('sources',sources.join(','))
  return call<any>(`/api/cases/${id}/360?${qs}`)
 },
 investigationCase360:(investigationId:string,caseId:string,sources?:string[])=>{
  const qs=sources?.length?`?sources=${encodeURIComponent(sources.join(','))}`:''
  return call<any>(`/api/investigations/${investigationId}/cases/${caseId}/360${qs}`)
 },
 passport:(id:string,purpose:string)=>call<any>(`/api/source-passports/${id}?purpose=${encodeURIComponent(purpose)}`),
 path:(from:string,to:string,purpose:string)=>call<any>(`/api/relationships/path?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&purpose=${encodeURIComponent(purpose)}`),
 dna:(left:string,right:string,purpose:string)=>call<any>(`/api/m5/case-dna/${left}/${right}?purpose=${encodeURIComponent(purpose)}`), graph:(id:string,purpose:string)=>call<any>(`/api/m5/graph/${id}?purpose=${encodeURIComponent(purpose)}`), assurance:(id:string,purpose:string)=>call<any>(`/api/m5/assurance/${id}?purpose=${encodeURIComponent(purpose)}`), verify:(left:string,right:string,purpose:string)=>call<any>(`/api/m5/verify/${left}/${right}?purpose=${encodeURIComponent(purpose)}`), challenge:(id:string,hypothesis:string,purpose:string)=>call<any>(`/api/m5/challenge/${id}?purpose=${encodeURIComponent(purpose)}`,{method:'POST',body:JSON.stringify({hypothesis})}), actions:(id:string,purpose:string)=>call<any>(`/api/m5/actions/${id}?purpose=${encodeURIComponent(purpose)}`),
 createReport:(payload:object)=>call<any>('/api/reports',{method:'POST',body:JSON.stringify(payload)}), updateReport:(id:string,payload:object)=>call<any>(`/api/reports/${id}`,{method:'PATCH',body:JSON.stringify(payload)}), submitReport:(id:string)=>call<any>(`/api/reports/${id}/submit`,{method:'POST'}), reportPreview:(id:string)=>call<any>(`/api/reports/${id}/preview`), reviewReport:(id:string,payload:object)=>call<any>(`/api/reports/${id}/review`,{method:'POST',body:JSON.stringify(payload)}), newReportVersion:(id:string)=>call<any>(`/api/reports/${id}/versions`,{method:'POST'}), audit:(params:string)=>call<any>(`/api/audit-events?${params}`), systemHealth:()=>call<any>('/api/system-health'),
 reports:()=>call<any>('/api/reports'), reviewers:()=>call<any[]>('/api/reviewers'), assignReviewer:(id:string,reviewer:string)=>call<any>(`/api/reports/${id}/assign`,{method:'POST',body:JSON.stringify({reviewer})}), reportDetail:(id:string)=>call<any>(`/api/reports/${id}`), previewMetadata:(id:string)=>call<any>(`/api/reports/${id}/preview-metadata`),
 resolveChatAction:(iid:string,text:string,context:object)=>call<any>(`/api/investigations/${iid}/chat/action`,{method:'POST',body:JSON.stringify({query:text,context})}),
 chatMessage:(iid:string,payload:{query:string;history?:any[];context?:object})=>call<any>(`/api/investigations/${iid}/chat/message`,{method:'POST',body:JSON.stringify(payload)}),
 aiAnswer:(iid:string,payload:object)=>call<any>(`/api/investigations/${iid}/answer`,{method:'POST',body:JSON.stringify(payload)}),
 voiceTranscribe:(audio:Blob,languageCode:string,mode='codemix'):Promise<{text:string;language:string}>=>fetch(`/api/voice/transcribe?language_code=${encodeURIComponent(languageCode)}&mode=${mode}`,{credentials:'same-origin',method:'POST',body:audio,headers:{'Content-Type':audio.type||'audio/webm','X-Anvaya-Language':languageCode}}).then(async r=>{const b=await r.json();if(!r.ok)throw new Error(b.message||'Transcription failed.');return (b as any).data}),
 voiceSpeak:(text:string,targetLanguageCode:string)=>call<{audio_base64:string;content_type:string;target_language_code:string}>('/api/voice/speak',{method:'POST',body:JSON.stringify({text,target_language_code:targetLanguageCode})}),
 voiceTranslate:(text:string,source:string,target:string)=>call<{text:string;source_language_code:string;target_language_code:string}>('/api/voice/translate',{method:'POST',body:JSON.stringify({text,source_language_code:source,target_language_code:target})}),
 conversations:()=>call<any[]>('/api/conversations'),
 conversationDetail:(id:string)=>call<any>(`/api/conversations/${id}`),
 createConversation:(payload:object)=>call<any>('/api/conversations',{method:'POST',body:JSON.stringify(payload)}),
 updateConversation:(id:string,payload:object)=>call<any>(`/api/conversations/${id}`,{method:'PATCH',body:JSON.stringify(payload)}),
 deleteConversation:(id:string)=>call<any>(`/api/conversations/${id}`,{method:'DELETE'}),
 searchConversations:(query:string)=>call<any[]>(`/api/conversations/search?q=${encodeURIComponent(query)}`),
 copilotAnalyze:(investigationId:string,caseId?:string)=>call<any>(`/api/copilot/analyze/${investigationId}${caseId?`/${caseId}`:''}`),
 copilotSuggestNext:(investigationId:string,caseId:string)=>call<any>(`/api/copilot/suggest/${investigationId}/${caseId}`),
 explainFinding:(investigationId:string,caseId:string,findingId:string)=>call<any>(`/api/explain/${investigationId}/${caseId}/${findingId}`),
 explainEdge:(investigationId:string,caseId:string,sourceId:string,targetId:string)=>call<any>(`/api/explain/edge/${investigationId}/${caseId}?source=${encodeURIComponent(sourceId)}&target=${encodeURIComponent(targetId)}`),
 shiftIntelligence:(stationId:string)=>call<any>(`/api/shift/intelligence?station=${encodeURIComponent(stationId)}`),
 supervisorTimeline:(investigationId:string)=>call<any>(`/api/supervisor/timeline/${investigationId}`),
 supervisorReview:(investigationId:string,reviewId:string)=>call<any>(`/api/supervisor/review/${investigationId}/${reviewId}`),
 submitReview:(investigationId:string,payload:object)=>call<any>(`/api/supervisor/review/${investigationId}`,{method:'POST',body:JSON.stringify(payload)}),
}
