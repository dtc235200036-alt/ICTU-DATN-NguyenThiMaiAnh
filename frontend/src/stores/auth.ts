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

interface AuthState {
  accessToken: string | null
  user: NguoiDung | null
  setSession: (token: string, user: NguoiDung) => void
  clear: () => void
}

// D-07: access token và user sống chỉ trong bộ nhớ (zustand, không persist)
// — không bao giờ ghi vào localStorage/sessionStorage.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setSession: (token, user) => set({ accessToken: token, user }),
  clear: () => set({ accessToken: null, user: null }),
}))
