import { createHttpClient } from './http'
import type { Bot } from '../types/Bot'

const client = createHttpClient()

export function fetchRecent(): Promise<Bot[]> {
  return client.request({ method: 'get', url: '/bots/recent' })
}
