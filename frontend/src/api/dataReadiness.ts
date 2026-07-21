export type ImportFailure={row:number;category:string;reason:string}
export type ImportJob={id:string;input_format:string;mapped_fields:string[];missing_required_keys:string[];accepted_count:number;failed_count:number;failures:ImportFailure[];status:string;import_timestamp:string;checksum:string;source_version:string;committed_at:string|null}
export type SourceMetadata={id:string;name:string;status:'Fresh'|'Stale'|'Unavailable';priority:'P0'|'P1';version:string}
type Envelope<T>={request_id:string;data:T;warnings:string[]}

async function unwrap<T>(response:Response):Promise<T>{
  const body=await response.json()
  if(!response.ok) throw new Error(body.message ?? 'Data Readiness request failed.')
  return (body as Envelope<T>).data
}
export async function listSources(){return unwrap<SourceMetadata[]>(await fetch('/api/sources'))}
export async function validateFile(file:File){const form=new FormData();form.append('file',file);return unwrap<ImportJob>(await fetch('/api/imports/validate',{method:'POST',body:form}))}
export async function commitImport(id:string){return unwrap<ImportJob>(await fetch(`/api/imports/${id}/commit`,{method:'POST'}))}
