import axios, { AxiosError } from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'

import { useAuthStore } from '../stores/auth'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// D-07: các endpoint không bao giờ tự kích hoạt vòng refresh (tránh vòng lặp
// vô hạn khi chính /auth/refresh hoặc /auth/login trả 401).
const NO_REFRESH_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout']

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
}

let refreshPromise: Promise<boolean> | null = null

/**
 * Single-flight: nhiều request 401 đồng thời chỉ gọi POST /auth/refresh một lần.
 * Trả về true khi phiên được khôi phục (setSession đã chạy), false khi thất bại
 * (clear() đã chạy — RequireAuth sẽ điều hướng /dang-nhap).
 */
export function refreshSession(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = api
    .post('/auth/refresh')
    .then(({ data }) => {
      useAuthStore.getState().setSession(data.access_token, data.nguoi_dung)
      return true
    })
    .catch(() => {
      useAuthStore.getState().clear()
      return false
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined
    const url = config?.url ?? ''
    const isAuthLifecycleRequest = NO_REFRESH_PATHS.some((path) => url.startsWith(path))

    if (error.response?.status === 401 && config && !config._retried && !isAuthLifecycleRequest) {
      config._retried = true
      const ok = await refreshSession()
      if (ok) {
        const token = useAuthStore.getState().accessToken
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return api(config)
      }
    }

    return Promise.reject(error)
  },
)

export function getErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
  }
  return 'Đã xảy ra lỗi. Vui lòng thử lại sau.'
}
