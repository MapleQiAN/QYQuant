import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as payments from './payments'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('./http', () => ({
  createHttpClient: () => ({ request: requestMock })
}))

describe('payments api', () => {
  beforeEach(() => {
    requestMock.mockClear()
    requestMock.mockResolvedValue({ ok: true })
  })

  it('calls create payment order endpoint with plan and provider', async () => {
    requestMock.mockResolvedValueOnce({
      order_id: 'ord-123',
      pay_url: 'https://pay.mock.example.com/wechat/lite?amount=200',
      plan_level: 'lite',
      amount: 200,
      provider: 'wechat',
    })

    const data = await payments.createPaymentOrder({ plan_level: 'lite', provider: 'wechat' })

    expect(data.order_id).toBe('ord-123')
    expect(data.amount).toBe(200)
    expect(requestMock).toHaveBeenCalledWith({
      method: 'post',
      url: '/v1/payments/orders',
      data: { plan_level: 'lite', provider: 'wechat' },
    })
  })
})
