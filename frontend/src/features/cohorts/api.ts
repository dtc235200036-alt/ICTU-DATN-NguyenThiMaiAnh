import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'

export type CohortState = 'DANG_MO' | 'DA_DONG'

export interface CohortOut {
  id: number
  ten_dot: string
  khoa: string
  nam_hoc: string | null
  ngay_bat_dau: string
  ngay_ket_thuc: string | null
  trang_thai: CohortState
}

export interface CohortFormInput {
  ten_dot: string
  khoa: string
  nam_hoc?: string | null
  ngay_bat_dau: string
  ngay_ket_thuc?: string | null
}

export interface CohortsQueryParams {
  trang_thai?: CohortState
  khoa?: string
}

const COHORTS_KEY = 'cohorts'

// Dùng lại ở các plan 02-04/02-05 (bộ lọc/form đề tài cần đợt đang mở).
export function useCohorts(params?: CohortsQueryParams) {
  return useQuery({
    queryKey: [COHORTS_KEY, params],
    queryFn: async () => {
      const { data } = await api.get<CohortOut[]>('/cohorts', { params })
      return data
    },
  })
}

export function useCreateCohort() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: CohortFormInput) => {
      const { data } = await api.post<CohortOut>('/cohorts', input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [COHORTS_KEY] })
    },
  })
}

export function useUpdateCohort() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, input }: { id: number; input: CohortFormInput }) => {
      const { data } = await api.put<CohortOut>(`/cohorts/${id}`, input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [COHORTS_KEY] })
    },
  })
}

export function useSetCohortState() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, action }: { id: number; action: 'open' | 'close' }) => {
      const { data } = await api.post<CohortOut>(`/cohorts/${id}/${action}`)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [COHORTS_KEY] })
    },
  })
}
