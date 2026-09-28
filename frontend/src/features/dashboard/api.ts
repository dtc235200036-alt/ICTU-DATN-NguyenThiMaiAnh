import { useQuery } from '@tanstack/react-query'

import { api } from '../../api/client'

export interface SvTopicOut {
  id: number
  ten_de_tai: string
  trang_thai: string
  giang_vien_huong_dan: string | null
  ly_do_tu_choi: string | null
}

export interface SvDashboardOut {
  de_tai: SvTopicOut | null
  co_dot_dang_mo: boolean
}

export interface GvTopicItem {
  id: number
  ten_de_tai: string
  trang_thai: string
  sinh_vien: string | null
}

export interface GvDashboardOut {
  so_sinh_vien_huong_dan: number
  so_de_tai: number
  so_de_tai_cho_duyet: number
  de_tai: GvTopicItem[]
}

export interface BmPendingTopicRef {
  id: number
  ten_de_tai: string
  nguoi_de_xuat: string
}

export interface DashboardCohortRef {
  id: number
  ten_dot: string
  khoa: string
  trang_thai: 'DANG_MO' | 'DA_DONG'
}

export interface BmDashboardOut {
  dot_do_an: DashboardCohortRef | null
  de_tai_cho_duyet: number
  de_tai_da_phan_cong: number
  sv_chua_co_de_tai: number
  tong_sinh_vien: number
  cho_duyet_moi_nhat: BmPendingTopicRef[]
}

export function useSvDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'sinh-vien'],
    queryFn: async () => {
      const { data } = await api.get<SvDashboardOut>('/dashboard/sinh-vien')
      return data
    },
  })
}

export function useGvDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'giang-vien'],
    queryFn: async () => {
      const { data } = await api.get<GvDashboardOut>('/dashboard/giang-vien')
      return data
    },
  })
}

export function useBmDashboard(dotDoAnId?: number) {
  return useQuery({
    queryKey: ['dashboard', 'bo-mon', dotDoAnId],
    queryFn: async () => {
      const { data } = await api.get<BmDashboardOut>('/dashboard/bo-mon', {
        params: dotDoAnId ? { dot_do_an_id: dotDoAnId } : undefined,
      })
      return data
    },
  })
}
