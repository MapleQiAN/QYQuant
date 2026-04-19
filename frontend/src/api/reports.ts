import { createHttpClient } from './http'
import type {
  BacktestAiReportResponse,
  BacktestAiReportStatusResponse,
} from '../types/Backtest'

const client = createHttpClient()

export function fetchReport(reportId: string): Promise<BacktestAiReportResponse> {
  return client.request({ method: 'get', url: `/reports/${reportId}` })
}

export function fetchReportStatus(reportId: string): Promise<BacktestAiReportStatusResponse> {
  return client.request({ method: 'get', url: `/reports/${reportId}/status` })
}

export function openReportStatusStream(
  reportId: string,
  onMessage: (payload: BacktestAiReportStatusResponse) => void,
  onError?: (event: Event) => void,
): EventSource {
  const token = typeof window !== 'undefined' ? localStorage.getItem('qyquant-token') || '' : ''
  const baseUrl = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')
  const url = `${baseUrl}/reports/${reportId}/status/stream?token=${encodeURIComponent(token)}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as BacktestAiReportStatusResponse)
    } catch {
      return
    }
  }

  if (onError) {
    eventSource.onerror = onError
  }

  return eventSource
}
