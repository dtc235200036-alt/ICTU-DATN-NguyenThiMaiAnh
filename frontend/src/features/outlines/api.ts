import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import { downloadFile } from '../../api/download'
import type { DinhHuongRef } from '../dinh-huong/api'
import type {
  CheckDetail,
  CheckMatch,
  CheckSegment,
  CheckStatus,
  CheckSummary,
  DocumentOut,
  PersonRef,
} from '../documents/api'

// Các kiểu tài liệu/kiểm tra trùng lặp giờ khai báo MỘT nơi duy nhất ở
// features/documents/api.ts (dùng chung với báo cáo tiến độ/cuối/chấm điểm ở
// các plan sau) — re-export lại đây để mọi import cũ từ 'features/outlines/api'
// không phải sửa.
export type { CheckDetail, CheckMatch, CheckSegment, CheckStatus, CheckSummary, DocumentOut, PersonRef }

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
  nop_bo_mon: boolean
  duyet_bo_mon: boolean
}

export type OutlineTrangThai =
  | 'CHUA_NOP'
  | 'CHO_DUYET'
  | 'YEU_CAU_SUA'
  | 'GVHD_DA_DUYET'
  | 'CHO_BO_MON_DUYET'
  | 'DA_DUYET'

/** Lọc tab "Từ chối" của Bộ môn (đề cương Bộ môn đã trả lại). */
export type OutlineFilter = OutlineTrangThai | 'BO_MON_TRA_LAI'

export interface BoMonReviewOut {
  ket_qua: 'DA_DUYET' | 'TRA_LAI'
  nhan_xet: string | null
  thoi_diem: string
  nguoi_duyet: string
  tai_lieu_id: number
  tai_lieu_ky_so: DocumentOut | null
  nguoi_ky: string | null
  thoi_diem_ky: string | null
}

export interface CheckItem {
  ma: 'TEN_FILE' | 'DINH_HUONG' | 'NOI_DUNG' | string
  ten: string
  dat: boolean
  chi_tiet: string | null
}

export interface OutlineCounts {
  tat_ca: number
  theo_trang_thai: Partial<Record<OutlineTrangThai, number>>
  bo_mon_tra_lai: number
}

export interface OutlineDetail {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  trang_thai: OutlineTrangThai
  ngay_nop_dau_tien: string | null
  phien_ban: OutlineVersion[]
  quyen: QuyenDeCuongOut
  dinh_huong: DinhHuongRef | null
  lop: string | null
  nop_bo_mon_luc: string | null
  ket_qua_bo_mon: 'DA_DUYET' | 'TRA_LAI' | null
  luot_duyet_bo_mon: BoMonReviewOut[]
  kiem_tra_nop: CheckItem[]
  ten_file_mau: string | null
}

export interface OutlineListItem {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  trang_thai: OutlineTrangThai
  phien_ban_moi_nhat: DocumentOut | null
  kiem_tra: CheckSummary | null
  dinh_huong: DinhHuongRef | null
  nop_bo_mon_luc: string | null
  ket_qua_bo_mon: 'DA_DUYET' | 'TRA_LAI' | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface OutlinesQueryParams {
  trang_thai?: OutlineFilter
  dot_do_an_id?: number
  q?: string
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

export function useOutlineCounts(params: { dot_do_an_id?: number; q?: string }) {
  return useQuery({
    queryKey: [OUTLINE_KEY, 'counts', params],
    queryFn: async () => {
      const { data } = await api.get<OutlineCounts>('/outlines/counts', { params })
      return data
    },
  })
}

function useOutlineMutation<V extends { deTaiId: number }>(
  fn: (variables: V) => Promise<OutlineDetail>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: [OUTLINE_KEY] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
      void variables
    },
  })
}

/** GVHD nộp đề cương đã duyệt lên Bộ môn. */
export function useForwardOutline() {
  return useOutlineMutation(async ({ deTaiId }: { deTaiId: number }) => {
    const { data } = await api.post<OutlineDetail>(`/outlines/${deTaiId}/forward`)
    return data
  })
}

/** Lãnh đạo bộ môn phê duyệt kèm bản PDF đã ký số. */
export function useBoMonApprove() {
  return useOutlineMutation(
    async ({ deTaiId, file, nhanXet }: { deTaiId: number; file: File; nhanXet?: string }) => {
      const formData = new FormData()
      formData.append('file', file)
      if (nhanXet) formData.append('nhan_xet', nhanXet)
      const { data } = await api.post<OutlineDetail>(
        `/outlines/${deTaiId}/bo-mon/approve`,
        formData,
      )
      return data
    },
  )
}

export function useBoMonReturn() {
  return useOutlineMutation(async ({ deTaiId, nhanXet }: { deTaiId: number; nhanXet: string }) => {
    const { data } = await api.post<OutlineDetail>(`/outlines/${deTaiId}/bo-mon/return`, {
      nhan_xet: nhanXet,
    })
    return data
  })
}

/** Thư mục đề cương đã ký số của một đợt (ZIP) — nộp về khoa. */
export function exportSignedOutlines(dotDoAnId: number) {
  return downloadFile(
    `/outlines/export-signed?dot_do_an_id=${dotDoAnId}`,
    `de-cuong-ky-so-dot-${dotDoAnId}.zip`,
  )
}

export function useSubmitOutline() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      deTaiId,
      file,
      ghiChu,
    }: {
      deTaiId: number
      file: File
      ghiChu?: string
    }) => {
      const formData = new FormData()
      formData.append('file', file)
      if (ghiChu) formData.append('ghi_chu', ghiChu)
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
