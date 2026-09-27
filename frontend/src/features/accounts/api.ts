import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'

export type VaiTroAccount = 'SINH_VIEN' | 'GIANG_VIEN'

export interface AccountOut {
  tai_khoan_id: number
  vai_tro: VaiTroAccount
  ma_dang_nhap: string
  email: string
  bi_khoa: boolean
  profile_id: number
  ho_ten: string
  lop: string | null
  khoa: string | null
  hoc_vi: string | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface AccountCreateInput {
  vai_tro: VaiTroAccount
  ma: string
  email: string
  ho_ten: string
  lop?: string | null
  khoa?: string | null
  hoc_vi?: string | null
  mat_khau: string
}

export interface AccountUpdateInput {
  email?: string
  ho_ten?: string
  lop?: string | null
  khoa?: string | null
  hoc_vi?: string | null
  mat_khau?: string
}

export interface AccountsQueryParams {
  vai_tro: VaiTroAccount
  q?: string
  bi_khoa?: boolean
  page?: number
  page_size?: number
}

export interface LecturerOut {
  id: number
  ma_giang_vien: string | null
  ho_ten: string | null
  hoc_vi: string | null
}

const ACCOUNTS_KEY = 'accounts'
const LECTURERS_KEY = 'lecturers'

export function useAccounts(params: AccountsQueryParams) {
  return useQuery({
    queryKey: [ACCOUNTS_KEY, params],
    queryFn: async () => {
      const { data } = await api.get<PageResult<AccountOut>>('/accounts', { params })
      return data
    },
  })
}

export function useCreateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: AccountCreateInput) => {
      const { data } = await api.post<AccountOut>('/accounts', input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ACCOUNTS_KEY] })
    },
  })
}

export function useUpdateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, input }: { id: number; input: AccountUpdateInput }) => {
      const { data } = await api.put<AccountOut>(`/accounts/${id}`, input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ACCOUNTS_KEY] })
    },
  })
}

export function useSetAccountLocked() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, locked }: { id: number; locked: boolean }) => {
      const { data } = await api.post<AccountOut>(`/accounts/${id}/${locked ? 'lock' : 'unlock'}`)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ACCOUNTS_KEY] })
    },
  })
}

// Dùng lại ở các plan 02-05/02-06 (bộ lọc đề tài, gán GVHD).
export function useLecturers() {
  return useQuery({
    queryKey: [LECTURERS_KEY],
    queryFn: async () => {
      const { data } = await api.get<LecturerOut[]>('/lecturers')
      return data
    },
    staleTime: 5 * 60 * 1000,
  })
}
