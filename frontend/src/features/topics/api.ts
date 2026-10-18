import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import type { DinhHuongRef } from '../dinh-huong/api'

export interface PersonRef {
  id: number
  ho_ten: string
  ma: string | null
}

export interface CohortRef {
  id: number
  ten_dot: string
  khoa: string
  trang_thai: 'DANG_MO' | 'DA_DONG'
}

export interface QuyenOut {
  sua: boolean
  gui: boolean
}

export type TitleCheckStatus = 'HOAN_TAT' | 'LOI'

/** AISV-03: DE_TAI = đề tài hiện hành, KHO = đồ án trong kho các khóa trước. */
export type TitleMatchSource = 'DE_TAI' | 'KHO'

export interface TitleMatch {
  nguon: TitleMatchSource
  de_tai_id: number | null
  do_an_kho_id: number | null
  ten_de_tai: string
  khoa: string
  giang_vien: string | null
  ty_le: number
}

export interface TitleCheckResult {
  trang_thai: TitleCheckStatus
  nguong: number
  matches: TitleMatch[]
}

export interface SavedChiTietTrungLap {
  doi_tuong_trung: string
  ty_le: number
}

export interface SavedTitleCheck {
  trang_thai: TitleCheckStatus
  ty_le_tong: number | null
  nguong_ap_dung: number
  thoi_diem: string
  chi_tiet: SavedChiTietTrungLap[]
}

export interface TopicOut {
  id: number
  dot_do_an: CohortRef
  ten_de_tai: string
  mo_ta: string | null
  linh_vuc: string | null
  dinh_huong: DinhHuongRef | null
  tep_dinh_kem: TepDinhKem | null
  ngay_giao: string | null
  trang_thai: 'NHAP' | 'CHO_DUYET' | 'DA_DUYET' | 'TU_CHOI' | 'DA_PHAN_CONG'
  loai_nguoi_de_xuat: 'GIANG_VIEN' | 'SINH_VIEN'
  nguoi_de_xuat: PersonRef
  giang_vien_huong_dan: PersonRef | null
  sinh_vien: PersonRef | null
  ly_do_tu_choi: string | null
  quyen: QuyenOut
  kiem_tra_ten: SavedTitleCheck | null
}

export interface TepDinhKem {
  id: number
  ten_goc: string
  kich_thuoc: number
  dinh_dang: 'DOCX' | 'PDF'
  thoi_diem_nop: string
}

export interface TopicListItem {
  id: number
  ten_de_tai: string
  linh_vuc: string | null
  dinh_huong: DinhHuongRef | null
  trang_thai: TopicOut['trang_thai']
  dot_do_an: CohortRef
  nguoi_de_xuat: PersonRef
  giang_vien_huong_dan: PersonRef | null
  sinh_vien: PersonRef | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface TopicsQueryParams {
  dot_do_an_id?: number
  trang_thai?: string
  giang_vien_id?: number
  linh_vuc?: string
  dinh_huong_id?: number
  q?: string
  pham_vi?: 'tat_ca' | 'cua_toi'
  sap_xep?: 'moi_nhat' | 'ten'
  page?: number
  page_size?: number
}

export interface TopicFormInput {
  dot_do_an_id: number
  ten_de_tai: string
  mo_ta?: string | null
  linh_vuc?: string | null
  dinh_huong_id?: number | null
  // UC0.8/UC1.1: GVHD giao cho SV trong lớp hướng dẫn của mình (bắt buộc).
  sinh_vien_id: number
}

export interface TopicCreateInput extends TopicFormInput {
  gui: boolean
}

const TOPIC_KEY = 'topics'

export function useTopic(id: number | undefined) {
  return useQuery({
    queryKey: [TOPIC_KEY, id],
    queryFn: async () => {
      const { data } = await api.get<TopicOut>(`/topics/${id}`)
      return data
    },
    enabled: id !== undefined,
    // T-02-23: 403/404 là kết quả cuối cùng của server (không phải lỗi mạng
    // tạm thời) — không retry, để TopicDetailPage chuyển sang ForbiddenPage
    // ngay thay vì kẹt ở Skeleton qua nhiều lần thử lại.
    retry: (failureCount, error) => {
      const status = error instanceof AxiosError ? error.response?.status : undefined
      if (status !== undefined && status < 500) {
        return false
      }
      return failureCount < 3
    },
  })
}

// MH-05/UC1.2: danh sách đề tài lọc theo trạng thái/đợt/GVHD/lĩnh vực/từ khóa;
// placeholderData giữ trang cũ khi đổi bộ lọc/trang để tránh flash rỗng.
export function useTopics(params: TopicsQueryParams) {
  return useQuery({
    queryKey: [TOPIC_KEY, 'list', params],
    queryFn: async () => {
      const { data } = await api.get<PageResult<TopicListItem>>('/topics', { params })
      return data
    },
    placeholderData: keepPreviousData,
  })
}

export function useCreateTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: TopicCreateInput) => {
      const { data } = await api.post<TopicOut>('/topics', input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY] })
    },
  })
}

export function useUpdateTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, input }: { id: number; input: TopicFormInput }) => {
      const { data } = await api.put<TopicOut>(`/topics/${id}`, input)
      return data
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY, variables.id] })
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY] })
    },
  })
}

export function useCheckTitle() {
  return useMutation({
    mutationFn: async (ten_de_tai: string) => {
      const { data } = await api.post<TitleCheckResult>('/topics/check-title', { ten_de_tai })
      return data
    },
  })
}

export function useSubmitTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<TopicOut>(`/topics/${id}/submit`)
      return data
    },
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY, id] })
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY] })
    },
  })
}

/** GVHD đính kèm file mô tả đề tài (DOCX/PDF). */
export function useAttachTopicFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, file }: { id: number; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post<TopicOut>(`/topics/${id}/attachment`, formData)
      return data
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY, variables.id] })
    },
  })
}

export interface TopicEvent {
  thoi_diem: string
  noi_dung: string
  nguoi_thuc_hien: string
}

/** Lịch sử đề tài: giao đề tài, nộp/duyệt đề cương, Bộ môn phê duyệt, báo cáo. */
export function useTopicHistory(id: number | undefined) {
  return useQuery({
    queryKey: [TOPIC_KEY, id, 'history'],
    queryFn: async () => {
      const { data } = await api.get<TopicEvent[]>(`/topics/${id}/history`)
      return data
    },
    enabled: id !== undefined,
  })
}
