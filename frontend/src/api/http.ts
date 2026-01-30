import axios, { type AxiosRequestConfig } from 'axios'
import { retry } from '../lib/retry'
import { normalizeError } from './normalizeError'

export function createHttpClient() {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || '/api',
    timeout: 8000
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      throw normalizeError(error)
    }
  )

  return {
    async request<T>(config: AxiosRequestConfig): Promise<T> {
      return retry(async () => {
        const response = await instance.request<{ code: number; message: string; data: T }>(config)
        return response.data.data
      }, { retries: 3, delays: [200, 400, 800] })
    }
  }
}

export type HttpClient = ReturnType<typeof createHttpClient>
