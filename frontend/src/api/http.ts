import axios, { type AxiosRequestConfig } from 'axios'
import { retry } from '../lib/retry'
import { normalizeError } from './normalizeError'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
  meta?: Record<string, unknown>
}

export interface ApiDataWithMeta<T> {
  data: T
  meta?: Record<string, unknown>
}

export interface HttpRequestConfig extends AxiosRequestConfig {
  retry?: boolean
}

export function createHttpClient() {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || '/api',
    timeout: 8000
  })

  instance.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('qyquant-token')
      if (token) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  })

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      throw normalizeError(error)
    }
  )

  return {
    async request<T>(config: HttpRequestConfig): Promise<T> {
      return requestWithPolicy(config, async (axiosConfig) => {
        const response = await instance.request<ApiEnvelope<T>>(axiosConfig)
        return response.data.data
      })
    },
    async requestWithMeta<T>(config: HttpRequestConfig): Promise<ApiDataWithMeta<T>> {
      return requestWithPolicy(config, async (axiosConfig) => {
        const response = await instance.request<ApiEnvelope<T>>(axiosConfig)
        return {
          data: response.data.data,
          meta: response.data.meta
        }
      })
    }
  }

  async function requestWithPolicy<T>(
    config: HttpRequestConfig,
    execute: (axiosConfig: AxiosRequestConfig) => Promise<T>
  ): Promise<T> {
    if (!shouldRetry(config)) {
      return execute(stripRetryFlag(config))
    }

    return retry(async () => execute(stripRetryFlag(config)), {
      retries: 3,
      delays: [200, 400, 800]
    })
  }
}

export type HttpClient = ReturnType<typeof createHttpClient>

function shouldRetry(config: HttpRequestConfig): boolean {
  if (config.retry === true) {
    return true
  }
  if (config.retry === false) {
    return false
  }

  const method = (config.method || 'get').toUpperCase()
  return method === 'GET' || method === 'HEAD' || method === 'OPTIONS'
}

function stripRetryFlag(config: HttpRequestConfig): AxiosRequestConfig {
  const { retry: _retry, ...axiosConfig } = config
  return axiosConfig
}
