import { createHttpClient } from './http'

const client = createHttpClient()

export type PlanLevel = 'free' | 'go' | 'plus' | 'pro' | 'ultra'
export type PaymentProvider = 'wechat' | 'alipay'

export interface CreatePaymentOrderRequest {
  plan_level: PlanLevel
  provider: PaymentProvider
}

export interface CreatePaymentOrderResponse {
  order_id: string
  pay_url: string
  plan_level: PlanLevel
  amount: number
  provider: PaymentProvider
}

export function createPaymentOrder(payload: CreatePaymentOrderRequest): Promise<CreatePaymentOrderResponse> {
  return client.request({
    method: 'post',
    url: '/v1/payments/orders',
    data: payload,
  })
}
