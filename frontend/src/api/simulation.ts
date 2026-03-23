import { createHttpClient } from './http'
import type { CreateBotPayload, SimulationBot } from '../types/Simulation'

const client = createHttpClient()

export function acceptSimDisclaimer(): Promise<{ ok?: boolean }> {
  return client.request({
    method: 'post',
    url: '/v1/simulation/disclaimer/accept'
  })
}

export function createSimBot(payload: CreateBotPayload): Promise<SimulationBot> {
  return client.request({
    method: 'post',
    url: '/v1/simulation/bots',
    data: payload
  })
}
