import { createHttpClient } from './http'

const client = createHttpClient()

export interface AdminHealthResponse {
  status: string
  scope: string
}

export function fetchAdminHealth(): Promise<AdminHealthResponse> {
  return client.request({
    method: 'get',
    url: '/v1/admin/health'
  })
}
