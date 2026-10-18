import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'

export interface DinhHuongRef {
  id: number
  ma: string
  ten: string
}

export interface DinhHuongOut extends DinhHuongRef {
  mo_ta: string | null
  hoat_dong: boolean
  so_de_tai: number
}

export interface DinhHuongInput {
  ma: string
  ten: string
  mo_ta?: string | null
  hoat_dong: boolean
}

const KEY = 'dinh-huong'

/** Danh mục định hướng (H01, H02, ...) — form giao đề tài chỉ lấy loại đang hoạt động. */
export function useDinhHuong(chiHoatDong = false) {
  return useQuery({
    queryKey: [KEY, chiHoatDong],
    queryFn: async () => {
      const { data } = await api.get<DinhHuongOut[]>('/dinh-huong', {
        params: chiHoatDong ? { chi_hoat_dong: true } : undefined,
      })
      return data
    },
  })
}

export function useSaveDinhHuong() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, input }: { id?: number; input: DinhHuongInput }) => {
      const { data } = id
        ? await api.put<DinhHuongOut>(`/dinh-huong/${id}`, input)
        : await api.post<DinhHuongOut>('/dinh-huong', input)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [KEY] })
    },
  })
}

export function dinhHuongLabel(item: DinhHuongRef | null | undefined): string {
  return item ? `${item.ma} — ${item.ten}` : '—'
}
