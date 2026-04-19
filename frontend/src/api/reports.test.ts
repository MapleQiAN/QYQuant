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

  it('opens ai report status stream with auth token', () => {
    const onMessage = vi.fn()

    const source = reports.openReportStatusStream('report-1', onMessage)

    expect(eventSourceMock).toHaveBeenCalledWith('/api/reports/report-1/status/stream?token=token-123')
    expect(source).toBeTruthy()
  })
})
