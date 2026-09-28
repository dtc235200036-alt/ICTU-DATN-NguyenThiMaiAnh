import { useQuery } from '@tanstack/react-query'

import { api } from '../../api/client'
import type { CheckSummary } from '../documents/api'
import type { MilestoneOut, ProgressRow } from '../progress/api'
import type { TrangThaiMoc } from '../progress/constants'

// Mirror app/schemas/dashboard.py (Phase 2 + widget Phase 3 của plan 03-07).

export interface SvTopicOut {
  id: number
  ten_de_tai: string
  trang_thai: string
  giang_vien_huong_dan: string | null
  ly_do_tu_choi: string | null
}

export interface SvOutlineOut {
  trang_thai: string
  phien_ban: number | null
  thoi_diem_nop: string | null
  kiem_tra: CheckSummary | null
}

export interface SvMilestoneStep {
  ten_moc: string
  han_nop: string | null
  trang_thai: TrangThaiMoc
}

export interface SvNextMilestone {
  ten_moc: string
  han_nop: string | null
  con_ngay: number | null
}

export interface SvDefenseOut {
  ten_hoi_dong: string
  phong: string
  ngay_bao_ve: string
  gio_du_kien: string
  chu_tich: string | null
  diem_trung_binh: number | null
}

export interface SvDashboardOut {
  de_tai: SvTopicOut | null
  co_dot_dang_mo: boolean
  de_cuong: SvOutlineOut | null
  tien_do: SvMilestoneStep[]
  moc_tiep_theo: SvNextMilestone | null
  bao_ve: SvDefenseOut | null
}

export interface GvTopicItem {
  id: number
  ten_de_tai: string
  trang_thai: string
  sinh_vien: string | null
}

export type LoaiViec = 'DUYET_DE_CUONG' | 'NHAN_XET_TIEN_DO' | 'CHAM_DIEM'

export interface GvTaskItem {
  loai: LoaiViec
  sinh_vien: string | null
  ten_de_tai: string
  ghi_chu: string
  lien_ket: string
}

export interface GvDashboardOut {
  so_sinh_vien_huong_dan: number
  so_de_tai: number
  so_de_tai_cho_duyet: number
  de_tai: GvTopicItem[]
  so_de_cuong_cho_duyet: number
  so_bao_cao_cho_nhan_xet: number
  so_hoi_dong_tham_gia: number
  viec_can_xu_ly: GvTaskItem[]
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

export interface BmUpcomingCommittee {
  id: number
  ten_hoi_dong: string
  ngay_bao_ve: string
  gio_bao_ve: string
  phong: string
  so_sinh_vien: number
}

export interface BmProgressExcerpt {
  moc: MilestoneOut[]
  items: ProgressRow[]
  tong: number
}

export interface BmDashboardOut {
  dot_do_an: DashboardCohortRef | null
  de_tai_cho_duyet: number
  de_tai_da_phan_cong: number
  sv_chua_co_de_tai: number
  tong_sinh_vien: number
  cho_duyet_moi_nhat: BmPendingTopicRef[]
  sv_tre_moc: number
  tien_do_trich: BmProgressExcerpt | null
  moc_tien_do: MilestoneOut[]
  so_hoi_dong_sap_toi: number
  hoi_dong_sap_toi: BmUpcomingCommittee[]
  /** WR-06: tài liệu đã kiểm tra xong nhưng chưa vào chỉ mục AI */
  tai_lieu_chua_index: number
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
