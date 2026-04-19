import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as reports from './reports'

const { requestMock, eventSourceMock } = vi.hoisted(() => {
  const requestMock = vi.fn().mockResolvedValue({ ok: true })
  const eventSourceMock = vi.fn().mockImplementation((url: string) => ({
    url,
    onmessage: null,
    onerror: null,
    close: vi.fn(),
  }))

  return { requestMock, eventSourceMock }
})

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock }),
}))

describe('reports api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    eventSourceMock.mockClear()
    vi.stubGlobal('EventSource', eventSourceMock)
    localStorage.setItem('qyquant-token', 'token-123')
  })

  it('fetches ai report by report id', async () => {
    await reports.fetchReport('report-1')

    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/reports/report-1' })
  })

  it('fetches ai report status by report id', async () => {
    await reports.fetchReportStatus('report-1')

    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/reports/report-1/status' })
  })

  it('sends ai report chat messages', async () => {
    await reports.sendReportChatMessage('report-1', 'What is the main risk?')

    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/reports/report-1/chat',
      data: { message: 'What is the main risk?' },
    })
  })

  it('fetches ai report chat history', async () => {
    await reports.fetchReportChatHistory('report-1')

    expect(requestMock).toHaveBeenCalledWith({ method: 'get', url: '/reports/report-1/chat/history' })
  })

  it('fetches and dismisses ai report alerts', async () => {
    await reports.fetchReportAlerts('report-1')
    await reports.dismissReportAlert('report-1', 'alert-1')

    expect(requestMock).toHaveBeenNthCalledWith(1, { method: 'get', url: '/reports/report-1/alerts' })
    expect(requestMock).toHaveBeenNthCalledWith(2, { method: 'post', url: '/reports/report-1/alerts/alert-1/dismiss' })
  })

  it('opens ai report status stream with auth token', () => {
    const onMessage = vi.fn()

    const source = reports.openReportStatusStream('report-1', onMessage)

    expect(eventSourceMock).toHaveBeenCalledWith('/api/reports/report-1/status/stream?token=token-123')
    expect(source).toBeTruthy()
  })
})
