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

export interface SubscriptionResponse {
  id: string
  plan_level: PlanLevel
  status: string
  payment_provider: PaymentProvider | null
  starts_at: string | null
  ends_at: string | null
  created_at: string | null
}

export function fetchMySubscription(): Promise<SubscriptionResponse | null> {
  return client.request({
    method: 'get',
    url: '/v1/payments/me/subscription',
  })
}

export interface OrderItem {
  order_id: string
  plan_level: PlanLevel
  amount: number
  provider: PaymentProvider
  status: string
  created_at: string | null
}

export interface OrderListMeta {
  total: number
  page: number
  per_page: number
}

export async function fetchMyOrders(page = 1, perPage = 10): Promise<{ data: OrderItem[]; meta: OrderListMeta }> {
  const result = await client.requestWithMeta<OrderItem[]>({
    method: 'get',
    url: '/v1/payments/me/orders',
    params: { page, per_page: perPage },
  })
  return { data: result.data, meta: result.meta as unknown as OrderListMeta }
}
