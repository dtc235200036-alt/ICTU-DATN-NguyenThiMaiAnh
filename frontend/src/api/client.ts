import axios, { AxiosError } from 'axios'

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

export function getErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
  }
  return 'Đã xảy ra lỗi. Vui lòng thử lại sau.'
}
