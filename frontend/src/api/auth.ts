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
  phone?: string
  email?: string
  nickname: string
  plan_level: string
}

export type AuthIdentifier =
  | { phone: string; email?: never }
  | { email: string; phone?: never }

export type LoginRequest = AuthIdentifier & {
  code: string
  nickname?: string
}

export interface PasswordAuthRequest {
  email: string
  password: string
  nickname?: string
}

function normalizeIdentifier(identifier: string | AuthIdentifier): AuthIdentifier {
  if (typeof identifier === 'string') {
    return { phone: identifier }
  }
  return identifier
}

export async function sendCode(identifier: string | AuthIdentifier): Promise<SendCodeResponse> {
  const res = await instance.post('/v1/auth/send-code', normalizeIdentifier(identifier))
  return res.data.data
}

export async function login(
  identifierOrPayload: string | LoginRequest,
  code?: string,
  nickname?: string,
): Promise<{ data: LoginResponse; access_token: string }> {
  const payload =
    typeof identifierOrPayload === 'string'
      ? { phone: identifierOrPayload, code: code || '', ...(nickname ? { nickname } : {}) }
      : identifierOrPayload

  const res = await instance.post('/v1/auth/login', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}

export async function registerWithPassword(payload: PasswordAuthRequest): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/register/password', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}

export async function loginWithPassword(payload: Omit<PasswordAuthRequest, 'nickname'>): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/login/password', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}
