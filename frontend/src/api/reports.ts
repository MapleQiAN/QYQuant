import { createHttpClient } from './http'
import type {
  BacktestAiAlert,
  BacktestAiAlertsResponse,
  BacktestAiChatHistoryResponse,
  BacktestAiChatMessage,
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

export function sendReportChatMessage(reportId: string, message: string, locale = 'en'): Promise<BacktestAiChatMessage> {
  return client.request({ method: 'post', url: `/reports/${reportId}/chat`, data: { message, locale }, timeout: 60000 })
}

export function fetchReportChatHistory(reportId: string): Promise<BacktestAiChatHistoryResponse> {
  return client.request({ method: 'get', url: `/reports/${reportId}/chat/history` })
}

export function fetchReportAlerts(reportId: string): Promise<BacktestAiAlertsResponse> {
  return client.request({ method: 'get', url: `/reports/${reportId}/alerts` })
}

export function dismissReportAlert(reportId: string, alertId: string): Promise<BacktestAiAlert> {
  return client.request({ method: 'post', url: `/reports/${reportId}/alerts/${alertId}/dismiss` })
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
