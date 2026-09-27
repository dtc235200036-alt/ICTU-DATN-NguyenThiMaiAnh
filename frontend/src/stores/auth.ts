import { create } from 'zustand'

import type { VaiTro } from '../app/registry'

export interface NguoiDung {
  id: number
  vai_tro: VaiTro
  ma_dang_nhap: string
  email: string
  ho_ten: string
  sinh_vien_id: number | null
  giang_vien_id: number | null
}

export type AuthStatus = 'checking' | 'authenticated' | 'anonymous'

interface AuthState {
  status: AuthStatus
  accessToken: string | null
  user: NguoiDung | null
  setSession: (token: string, user: NguoiDung) => void
  clear: () => void
}

// D-07: access token và user sống chỉ trong bộ nhớ (zustand, không persist)
// — không bao giờ ghi vào bộ nhớ trình duyệt (Web Storage).
// status bắt đầu 'checking' để AuthBootstrap biết cần gọi /auth/refresh trước
// khi quyết định điều hướng tới /dang-nhap hay giữ nguyên trang hiện tại.
export const useAuthStore = create<AuthState>((set) => ({
  status: 'checking',
  accessToken: null,
  user: null,
  setSession: (token, user) => set({ status: 'authenticated', accessToken: token, user }),
  clear: () => set({ status: 'anonymous', accessToken: null, user: null }),
}))
