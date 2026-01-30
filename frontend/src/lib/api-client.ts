import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import axiosRetry from 'axios-retry'
import type { ApiResponse, ApiError } from '@/types'
import { toast } from './toast'

const API_TIMEOUT = 10000
const MAX_RETRIES = 3

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

axiosRetry(apiClient, {
  retries: MAX_RETRIES,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error: AxiosError) => {
    if (!error.response) return false

    const status = error.response.status
    return status === 429 || status >= 500
  },
  onRetry: (retryCount, error, requestConfig) => {
    console.log(
      `Retrying request (${retryCount}/${MAX_RETRIES}):`,
      requestConfig.url,
      error.message
    )
  }
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('qyquant-token')

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    return response
  },
  (error: AxiosError<ApiResponse>) => {
    const apiError: ApiError = {
      message: '请求失败，请稍后重试'
    }

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      apiError.message = '请求超时，请检查网络连接'
      apiError.statusCode = 408
      toast.error(apiError.message)
    } else if (error.response) {
      const { status, data } = error.response

      apiError.statusCode = status
      apiError.code = data?.error

      switch (status) {
        case 400:
          apiError.message = data?.error || '请求参数错误'
          toast.warning(apiError.message)
          break
        case 401:
          apiError.message = '未授权，请重新登录'
          toast.error(apiError.message)
          localStorage.removeItem('qyquant-token')
          window.location.href = '/login'
          break
        case 403:
          apiError.message = '无权限访问'
          toast.error(apiError.message)
          break
        case 404:
          apiError.message = '请求的资源不存在'
          toast.warning(apiError.message)
          break
        case 429:
          apiError.message = '请求过于频繁，请稍后再试'
          toast.warning(apiError.message)
          break
        case 500:
          apiError.message = '服务器错误，请稍后重试'
          toast.error(apiError.message)
          break
        case 502:
        case 503:
        case 504:
          apiError.message = '服务暂时不可用，请稍后重试'
          toast.error(apiError.message)
          break
        default:
          apiError.message = data?.error || '未知错误'
          toast.error(apiError.message)
      }
    } else if (error.request) {
      apiError.message = '网络错误，请检查网络连接'
      apiError.statusCode = 0
      toast.error(apiError.message)
    }

    return Promise.reject(apiError)
  }
)

export async function request<T = any>(
  config: AxiosRequestConfig
): Promise<T> {
  try {
    const response = await apiClient.request<ApiResponse<T>>(config)

    if (response.data?.success === false) {
      throw new Error(response.data?.error || '请求失败')
    }

    return response.data?.data as T
  } catch (error) {
    throw error
  }
}

export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'GET', url }),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'POST', url, data }),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PUT', url, data }),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PATCH', url, data }),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'DELETE', url })
}

export default apiClient
