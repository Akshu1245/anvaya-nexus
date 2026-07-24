import {afterEach,describe,expect,it,vi} from 'vitest'
import {m3Api} from '../api/m3'

describe('Catalyst CSRF forwarding',()=>{
 afterEach(()=>{vi.restoreAllMocks();document.cookie='ZD_CSRF_TOKEN=; Max-Age=0; Path=/'})

 it('forwards the Catalyst CSRF cookie on mutating requests',async()=>{
  document.cookie='ZD_CSRF_TOKEN=csrf-token; Path=/'
  const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({
   request_id:'test',
   warnings:[],
   data:{id:'INV-1',title:'Demo',purpose:'Active Case Investigation',selected_sources:[],assigned_station:null,assigned_district:null},
  }),{status:201,headers:{'Content-Type':'application/json'}}))

  await m3Api.createInvestigation({title:'Demo',purpose:'Active Case Investigation'})

  const options=fetchMock.mock.calls[0][1] as RequestInit
  expect(new Headers(options.headers).get('X-ZCSRF-TOKEN')).toBe('zcsrfp=csrf-token')
 })
})
