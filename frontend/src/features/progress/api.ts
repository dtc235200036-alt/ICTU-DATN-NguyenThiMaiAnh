import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import type { DocumentOut } from '../documents/api'
import type { CohortRef, PersonRef } from '../topics/api'
import type { DanhGia, TrangThaiMoc } from './constants'

// UC3/PROG-01..03: mirror app/schemas/progress.py.
export interface MilestoneOut {
  id: number
  dot_do_an_id: number
  ten_moc: string
  thu_tu: number
  han_nop: string | null
  so_bao_cao: number
}

export interface ReportOut {
  id: number
  noi_dung: string | null
  thoi_diem_nop: string
  nhan_xet: string | null
  danh_gia: DanhGia | null
  tep: DocumentOut | null
}

export interface MilestoneStatus {
  id: number
  ten_moc: string
  thu_tu: number
  han_nop: string | null
  trang_thai: TrangThaiMoc
  so_ngay_tre: number | null
  bao_cao: ReportOut | null
}

export interface TopicProgress {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  dot_do_an: CohortRef | null
  trang_thai_de_cuong: string
  moc: MilestoneStatus[]
  tre_moc: boolean
  co_the_nop: boolean
  ly_do: string | null
  co_the_nhan_xet: boolean
}

export interface MyProgress {
  de_tai: TopicProgress | null
}

export interface StudentProgressItem {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  so_cho_nhan_xet: number
  tre_moc: boolean
}

export interface ProgressCell {
  moc_id: number
  trang_thai: TrangThaiMoc
  bao_cao_id: number | null
}

export interface ProgressRow {
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  de_tai: { id: number; ten_de_tai: string }
  o: ProgressCell[]
  tre_moc: boolean
}

export interface ProgressDashboard {
  dot_do_an: CohortRef | null
  moc: MilestoneOut[]
  items: ProgressRow[]
  total: number
  page: number
  page_size: number
  so_sv_tre_moc: number
}

export interface DashboardParams {
  dot_do_an_id?: number
  chi_tre_moc?: boolean
  page?: number
  page_size?: number
}

const KEY = 'progress'

function noRetryOn4xx(failureCount: number, error: unknown): boolean {
  const status = error instanceof AxiosError ? error.response?.status : undefined
  if (status !== undefined && status < 500) return false
  return failureCount < 3
}

function useInvalidateProgress() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: [KEY] })
  }
}

export function useMilestones(dotDoAnId: number | undefined) {
  return useQuery({
    queryKey: [KEY, 'milestones', dotDoAnId],
    queryFn: async () => {
      const { data } = await api.get<MilestoneOut[]>('/progress/milestones', {
        params: { dot_do_an_id: dotDoAnId },
      })
      return data
    },
    enabled: dotDoAnId !== undefined,
    retry: noRetryOn4xx,
  })
}

export interface MilestoneInput {
  id?: number
  dot_do_an_id: number
  ten_moc: string
  han_nop: string
}

export function useSaveMilestone() {
  const invalidate = useInvalidateProgress()
  return useMutation({
    mutationFn: async ({ id, dot_do_an_id, ten_moc, han_nop }: MilestoneInput) => {
      if (id !== undefined) {
        const { data } = await api.put<MilestoneOut>(`/progress/milestones/${id}`, {
          ten_moc,
          han_nop,
        })
        return data
      }
      const { data } = await api.post<MilestoneOut>('/progress/milestones', {
        dot_do_an_id,
        ten_moc,
        han_nop,
      })
      return data
    },
    onSuccess: invalidate,
  })
}

export function useDeleteMilestone() {
  const invalidate = useInvalidateProgress()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/progress/milestones/${id}`)
    },
    onSuccess: invalidate,
  })
}

export function useMyProgress() {
  return useQuery({
    queryKey: [KEY, 'me'],
    queryFn: async () => {
      const { data } = await api.get<MyProgress>('/progress/me')
      return data
    },
    retry: noRetryOn4xx,
  })
}

export function useSubmitReport() {
  const invalidate = useInvalidateProgress()
  return useMutation({
    mutationFn: async ({ mocId, noiDung, file }: { mocId: number; noiDung: string; file?: File }) => {
      const form = new FormData()
      form.append('noi_dung', noiDung)
      if (file) form.append('file', file)
      const { data } = await api.post<MyProgress>(`/progress/reports/${mocId}`, form)
      return data
    },
    onSuccess: invalidate,
  })
}

export function useProgressStudents() {
  return useQuery({
    queryKey: [KEY, 'students'],
    queryFn: async () => {
      const { data } = await api.get<StudentProgressItem[]>('/progress/students')
      return data
    },
    retry: noRetryOn4xx,
  })
}

export function useTopicProgress(deTaiId: number | undefined) {
  return useQuery({
    queryKey: [KEY, 'topic', deTaiId],
    queryFn: async () => {
      const { data } = await api.get<TopicProgress>(`/progress/topics/${deTaiId}`)
      return data
    },
    enabled: deTaiId !== undefined,
    retry: noRetryOn4xx,
  })
}

export function useReviewReport() {
  const invalidate = useInvalidateProgress()
  return useMutation({
    mutationFn: async ({
      baoCaoId,
      nhanXet,
      danhGia,
    }: {
      baoCaoId: number
      nhanXet: string
      danhGia: DanhGia
    }) => {
      const { data } = await api.post<TopicProgress>(`/progress/reports/${baoCaoId}/review`, {
        nhan_xet: nhanXet,
        danh_gia: danhGia,
      })
      return data
    },
    onSuccess: invalidate,
  })
}

export function useProgressDashboard(params: DashboardParams) {
  return useQuery({
    queryKey: [KEY, 'dashboard', params],
    queryFn: async () => {
      const { data } = await api.get<ProgressDashboard>('/progress/dashboard', { params })
      return data
    },
    placeholderData: keepPreviousData,
    retry: noRetryOn4xx,
  })
}
