import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'
import type { CohortRef, PersonRef, TopicOut } from '../topics/api'

export interface AssignmentRow {
  sinh_vien: PersonRef
  lop: string | null
  giang_vien: PersonRef | null
  de_tai_id: number | null
  ten_de_tai: string | null
  trang_thai_de_tai: TopicOut['trang_thai'] | null
}

export interface LecturerLoad {
  giang_vien: PersonRef
  hoc_vi: string | null
  so_sinh_vien: number
}

export interface AssignmentPage {
  items: AssignmentRow[]
  total: number
  page: number
  page_size: number
  tong_sinh_vien: number
  da_phan_cong: number
  tai_giang_vien: LecturerLoad[]
}

export type AssignmentFilter = 'tat_ca' | 'da_phan_cong' | 'chua_phan_cong'

export interface AssignmentsQueryParams {
  dot_do_an_id: number
  q?: string
  giang_vien_id?: number
  loc?: AssignmentFilter
  page?: number
  page_size?: number
}

export interface AssignmentItem {
  sinh_vien_id: number
  giang_vien_id: number | null
}

export interface AssignmentResult {
  cap_nhat: number
  loi: string[]
}

export interface MyStudentItem {
  sinh_vien: PersonRef
  lop: string | null
  email: string | null
  de_tai_id: number | null
  ten_de_tai: string | null
  trang_thai_de_tai: TopicOut['trang_thai'] | null
}

export interface MyStudentsOut {
  dot_do_an: CohortRef
  items: MyStudentItem[]
}

export interface MyAdvisorOut {
  dot_do_an: CohortRef
  giang_vien: PersonRef
  hoc_vi: string | null
  email: string | null
  thoi_diem: string
}

const ASSIGN_KEY = 'assignments'

// UC0.8/MH-15: bảng phân công của một đợt (chỉ Bộ môn).
export function useAssignments(params: AssignmentsQueryParams | undefined) {
  return useQuery({
    queryKey: [ASSIGN_KEY, 'list', params],
    queryFn: async () => {
      const { data } = await api.get<AssignmentPage>('/assignments', { params })
      return data
    },
    enabled: params !== undefined,
    placeholderData: keepPreviousData,
  })
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: [ASSIGN_KEY] })
  void queryClient.invalidateQueries({ queryKey: ['topics'] })
}

export function useUpdateAssignments() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { dot_do_an_id: number; items: AssignmentItem[] }) => {
      const { data } = await api.put<AssignmentResult>('/assignments', input)
      return data
    },
    onSuccess: () => invalidate(queryClient),
  })
}

export function useImportAssignments() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { dot_do_an_id: number; noi_dung: string }) => {
      const { data } = await api.post<AssignmentResult>('/assignments/import', input)
      return data
    },
    onSuccess: () => invalidate(queryClient),
  })
}

// MH-16: lớp hướng dẫn của GV (mặc định mọi đợt đang mở).
export function useMyStudents(dotDoAnId?: number, enabled = true) {
  return useQuery({
    queryKey: [ASSIGN_KEY, 'my-students', dotDoAnId],
    queryFn: async () => {
      const { data } = await api.get<MyStudentsOut[]>('/assignments/my-students', {
        params: dotDoAnId !== undefined ? { dot_do_an_id: dotDoAnId } : undefined,
      })
      return data
    },
    enabled,
  })
}

// SV: GVHD của mình theo từng đợt (đợt mới nhất trước).
export function useMyAdvisor(enabled = true) {
  return useQuery({
    queryKey: [ASSIGN_KEY, 'my-advisor'],
    queryFn: async () => {
      const { data } = await api.get<MyAdvisorOut[]>('/assignments/my-advisor')
      return data
    },
    enabled,
  })
}
