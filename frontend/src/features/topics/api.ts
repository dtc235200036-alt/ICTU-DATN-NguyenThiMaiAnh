import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'

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

export interface TitleMatch {
  de_tai_id: number
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
  trang_thai: 'NHAP' | 'CHO_DUYET' | 'DA_DUYET' | 'TU_CHOI' | 'DA_PHAN_CONG'
  loai_nguoi_de_xuat: 'GIANG_VIEN' | 'SINH_VIEN'
  nguoi_de_xuat: PersonRef
  giang_vien_huong_dan: PersonRef | null
  sinh_vien: PersonRef | null
  ly_do_tu_choi: string | null
  quyen: QuyenOut
  kiem_tra_ten: SavedTitleCheck | null
}

export interface TopicFormInput {
  dot_do_an_id: number
  ten_de_tai: string
  mo_ta?: string | null
  linh_vuc?: string | null
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
