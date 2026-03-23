import { createHttpClient } from './http'
import type {
  CreateBotPayload,
  SimBotStreamPayload,
  SimulationBot,
  SimulationPosition,
  SimulationRecord,
  SimulationTrade,
} from '../types/Simulation'

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

export function getSimRecords(botId: string): Promise<SimulationRecord[]> {
  return client.request({
    method: 'get',
    url: `/v1/simulation/bots/${botId}/records`,
  })
}

export function getSimTrades(botId: string): Promise<SimulationTrade[]> {
  return client.request({
    method: 'get',
    url: `/v1/simulation/bots/${botId}/trades`,
  })
}

export function patchSimBot(botId: string, payload: { status: 'active' | 'paused' }): Promise<{ id: string; status: string }> {
  return client.request({
    method: 'patch',
    url: `/v1/simulation/bots/${botId}`,
    data: payload,
  })
}

export function deleteSimBot(botId: string): Promise<{ deleted: boolean }> {
  return client.request({
    method: 'delete',
    url: `/v1/simulation/bots/${botId}`,
  })
}

export function createBotStream(
  botId: string,
  accessToken: string,
  onMessage: (payload: SimBotStreamPayload) => void,
  onError?: (event: Event) => void,
): EventSource {
  const baseUrl = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')
  const url = `${baseUrl}/v1/simulation/bots/${botId}/stream?token=${encodeURIComponent(accessToken)}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as SimBotStreamPayload)
    } catch {
      return
    }
  }

  if (onError) {
    eventSource.onerror = onError
  }

  return eventSource
}
