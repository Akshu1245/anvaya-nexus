export type HealthEnvelope = {
  request_id: string
  data: {
    status: 'ok'
    service: 'anvaya-api'
    environment: 'development' | 'testing' | 'production'
    database: 'ok'
  }
  warnings: string[]
}

export async function fetchHealth(): Promise<HealthEnvelope> {
  const response = await fetch('/api/health', {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) {
    throw new Error('The ANVAYA API is unavailable.')
  }
  return response.json() as Promise<HealthEnvelope>
}
