import { createHttpClient } from './http'
import type { CreateBotPayload, SimulationBot, SimulationPosition } from '../types/Simulation'

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

export function getSimBots(): Promise<SimulationBot[]> {
  return client.request({
    method: 'get',
    url: '/v1/simulation/bots'
  })
}

export function getSimPositions(botId: string): Promise<SimulationPosition[]> {
  return client.request({
    method: 'get',
    url: `/v1/simulation/bots/${botId}/positions`
  })
}
