import axios, { type AxiosRequestConfig } from 'axios'
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
    async (error) => Promise.reject(error)
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
    const axiosConfig = stripRetryFlag(config)
    const maxAttempts = shouldRetry(config) ? 3 : 1

    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      try {
        return await executeWithAuthRecovery(axiosConfig, execute)
      } catch (error) {
        if (attempt >= maxAttempts - 1 || !isRetryableError(error)) {
          throw error
        }

        const delay = [200, 400, 800][attempt] ?? 800
        if (delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, delay))
        }
      }
    }

    throw new Error('Request retry loop exited unexpectedly')
  }

  async function executeWithAuthRecovery<T>(
    axiosConfig: AxiosRequestConfig,
    execute: (axiosConfig: AxiosRequestConfig) => Promise<T>
  ): Promise<T> {
    try {
      return await execute(axiosConfig)
    } catch (error) {
      if (!shouldRefreshAccessToken(error, axiosConfig)) {
        throw normalizeError(error)
      }

      try {
        const nextAccessToken = await refreshAccessToken()
        if (typeof window !== 'undefined') {
          localStorage.setItem('qyquant-token', nextAccessToken)
        }

        return await execute({
          ...axiosConfig,
          headers: {
            ...(axiosConfig.headers || {}),
            Authorization: `Bearer ${nextAccessToken}`
          }
        })
      } catch (refreshError) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('qyquant-token')
        }
        throw normalizeError(refreshError)
      }
    }
  }

  async function refreshAccessToken(): Promise<string> {
    const response = await instance.request<ApiEnvelope<{ access_token: string }>>({
      method: 'post',
      url: '/v1/auth/refresh',
      withCredentials: true
    })

    return response.data.data.access_token
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

function shouldRefreshAccessToken(error: any, config: AxiosRequestConfig): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const token = localStorage.getItem('qyquant-token')
  if (!token) {
    return false
  }

  const status = error?.response?.status
  const url = typeof config.url === 'string' ? config.url : ''
  return status === 401 && url !== '/v1/auth/refresh'
}

function isRetryableError(error: any): boolean {
  const status = error?.status ?? error?.response?.status
  if (typeof status !== 'number') {
    return true
  }

  return status === 408 || status === 429 || status >= 500
}
