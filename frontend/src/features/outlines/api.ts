import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import type { PersonRef } from '../topics/api'

export type { PersonRef }

export interface DocumentOut {
  id: number
  loai: string
  so_phien_ban: number
  ten_goc: string
  kich_thuoc: number
  dinh_dang: 'DOCX' | 'PDF'
  thoi_diem_nop: string
  trich_xuat_loi: boolean
  tom_tat: string | null
}

export type CheckStatus = 'DANG_KIEM_TRA' | 'HOAN_TAT' | 'LOI'

export interface CheckSummary {
  id: number
  trang_thai: CheckStatus
  ty_le_tong: number | null
  nguong_ap_dung: number
  thoi_diem: string
}

export interface CheckMatch {
  doi_tuong_trung: string
  ty_le: number
}

export interface CheckSegment {
  doi_tuong_trung: string
  doan_nguon: string | null
  doan_trung: string | null
  vi_tri: string | null
  ty_le: number
}

export interface CheckDetail extends CheckSummary {
  tai_lieu: DocumentOut
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  do_an_trung: CheckMatch[]
  chi_tiet: CheckSegment[]
}

export type ReviewKetQua = 'DA_DUYET' | 'YEU_CAU_SUA'

export interface ReviewOut {
  ket_qua: ReviewKetQua
  nhan_xet: string | null
  thoi_diem: string
  giang_vien: PersonRef
}

export interface OutlineVersion {
  tai_lieu: DocumentOut
  kiem_tra: CheckSummary | null
  luot_duyet: ReviewOut | null
}

export interface QuyenDeCuongOut {
  nop: boolean
  duyet: boolean
}

export type OutlineTrangThai = 'CHUA_NOP' | 'CHO_DUYET' | 'YEU_CAU_SUA' | 'DA_DUYET'

export interface OutlineDetail {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  trang_thai: OutlineTrangThai
  ngay_nop_dau_tien: string | null
  phien_ban: OutlineVersion[]
  quyen: QuyenDeCuongOut
}

export interface OutlineListItem {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  trang_thai: OutlineTrangThai
  phien_ban_moi_nhat: DocumentOut | null
  kiem_tra: CheckSummary | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface OutlinesQueryParams {
  trang_thai?: OutlineTrangThai
  dot_do_an_id?: number
  page?: number
  page_size?: number
}

const OUTLINE_KEY = 'outlines'

function hasPendingCheck(detail: OutlineDetail | undefined): boolean {
  if (!detail) return false
  return detail.phien_ban.some((version) => version.kiem_tra?.trang_thai === 'DANG_KIEM_TRA')
}

// MH-08/MH-09: danh sách đề cương theo phạm vi vai trò (server-side, xem
// outlines_service.list_outlines) — SV/GV chỉ thấy đề tài của mình.
export function useOutlines(params: OutlinesQueryParams) {
  return useQuery({
    queryKey: [OUTLINE_KEY, 'list', params],
    queryFn: async () => {
      const { data } = await api.get<PageResult<OutlineListItem>>('/outlines', { params })
      return data
    },
    placeholderData: keepPreviousData,
  })
}

// D-04: poll mỗi 3s trong khi phiên bản mới nhất còn Đang kiểm tra; không
// retry trên 4xx (403/404 là kết quả cuối cùng, không phải lỗi tạm thời).
export function useOutline(deTaiId: number | undefined) {
  return useQuery({
    queryKey: [OUTLINE_KEY, deTaiId],
    queryFn: async () => {
      const { data } = await api.get<OutlineDetail>(`/outlines/${deTaiId}`)
      return data
    },
    enabled: deTaiId !== undefined,
    refetchInterval: (query) => (hasPendingCheck(query.state.data) ? 3000 : false),
    retry: (failureCount, error) => {
      const status = error instanceof AxiosError ? error.response?.status : undefined
      if (status !== undefined && status < 500) {
        return false
      }
      return failureCount < 3
    },
  })
}

export function useSubmitOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ deTaiId, file }: { deTaiId: number; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      // Không tự đặt Content-Type: axios sẽ tự sinh boundary multipart đúng.
      const { data } = await api.post<OutlineDetail>(`/outlines/${deTaiId}/submit`, formData)
      return data
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: [OUTLINE_KEY, variables.deTaiId] })
      void queryClient.invalidateQueries({ queryKey: [OUTLINE_KEY, 'list'] })
    },
  })
}

export function useReviewOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      deTaiId,
      taiLieuDoAnId,
      ketQua,
      nhanXet,
    }: {
      deTaiId: number
      taiLieuDoAnId: number
      ketQua: ReviewKetQua
      nhanXet?: string
    }) => {
      const { data } = await api.post<OutlineDetail>(`/outlines/${deTaiId}/review`, {
        tai_lieu_do_an_id: taiLieuDoAnId,
        ket_qua: ketQua,
        nhan_xet: nhanXet,
      })
      return data
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: [OUTLINE_KEY, variables.deTaiId] })
      void queryClient.invalidateQueries({ queryKey: [OUTLINE_KEY, 'list'] })
    },
  })
}
