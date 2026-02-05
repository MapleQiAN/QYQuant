import { createHttpClient } from './http'
import type { Strategy, StrategyImportResult } from '../types/Strategy'

const client = createHttpClient()

export function fetchRecent(): Promise<Strategy[]> {
  return client.request({ method: 'get', url: '/strategies/recent' })
}

export function createStrategy(payload: {
  name: string
  symbol: string
  tags?: string[]
  status?: string
}): Promise<Strategy> {
  return client.request({ method: 'post', url: '/strategies', data: payload })
}

export function importStrategy(file: File): Promise<StrategyImportResult> {
  const form = new FormData()
  form.append('file', file)
  return client.request({
    method: 'post',
    url: '/strategies/import',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
