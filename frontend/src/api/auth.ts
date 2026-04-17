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

export interface ForgotPasswordResponse {
  message: string
}

export async function login(
  identifierOrPayload: string | PasswordAuthRequest | LoginRequest,
  code?: string,
  nickname?: string,
): Promise<{ data: LoginResponse; access_token: string }> {
  const payload =
    typeof identifierOrPayload === 'string'
      ? { email: identifierOrPayload, password: code || '', ...(nickname ? { nickname } : {}) }
      : identifierOrPayload

  const res = await instance.post('/v1/auth/login', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}

export async function registerWithPassword(payload: PasswordAuthRequest): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/register', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}

export async function loginWithPassword(payload: Omit<PasswordAuthRequest, 'nickname'>): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/login', payload)
  return { data: res.data.data, access_token: res.data.access_token }
}

export async function forgotPassword(email: string): Promise<ForgotPasswordResponse> {
  const res = await instance.post('/v1/auth/forgot-password', { email })
  return res.data.data
}

export async function resetPassword(token: string, password: string): Promise<{ message: string }> {
  const res = await instance.post('/v1/auth/reset-password', { token, password })
  return res.data.data
}

export async function initiateOAuth(provider: string): Promise<{ authorization_url: string }> {
  const res = await instance.get(`/v1/auth/oauth/${provider}`)
  return res.data.data
}

export async function completeOAuth(oauthToken: string): Promise<{ data: LoginResponse; access_token: string }> {
  const res = await instance.post('/v1/auth/oauth/complete', { oauth_token: oauthToken })
  return { data: res.data.data, access_token: res.data.access_token }
}
