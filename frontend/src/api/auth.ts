import axios from 'axios'
import { normalizeError } from './normalizeError'

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 8000,
})

instance.interceptors.response.use(
  (r) => r,
  (error) => { throw normalizeError(error) },
)

export interface SendCodeResponse {
  message: string
}

export interface LoginResponse {
  user_id: string
  phone: string
  nickname: string
  plan_level: string
}

export async function sendCode(phone: string): Promise<SendCodeResponse> {
  const res = await instance.post('/v1/auth/send-code', { phone })
  return res.data.data
}

export async function login(phone: string, code: string, nickname?: string): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/login', { phone, code, ...(nickname ? { nickname } : {}) })
  return { data: res.data.data, access_token: res.data.access_token }
}
