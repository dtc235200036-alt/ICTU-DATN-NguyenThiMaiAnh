import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'

export interface DinhHuongRef {
  id: number
  ma: string
  ten: string
}

/** File PDF mô tả định hướng do Bộ môn tải lên (0019). */
export interface TepDinhHuong {
  ten_goc: string
  kich_thuoc: number
  cap_nhat_luc: string
}

export interface DinhHuongOut extends DinhHuongRef {
  mo_ta: string | null
  hoat_dong: boolean
  so_de_tai: number
  /** null khi Bộ môn chưa tải lên file mô tả. */
  tep: TepDinhHuong | null
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

/** Đường dẫn dưới /api tới file PDF mô tả — xem (PdfBlobView) hoặc tải về. */
export function tepDinhHuongPath(id: number): string {
  return `/dinh-huong/${id}/tep`
}

/** Bộ môn tải lên hoặc thay file PDF mô tả định hướng. */
export function useUploadTepDinhHuong() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, file }: { id: number; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      // Không tự đặt Content-Type: axios sẽ tự sinh boundary multipart đúng.
      const { data } = await api.post<DinhHuongOut>(tepDinhHuongPath(id), formData)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [KEY] })
    },
  })
}

export function useDeleteTepDinhHuong() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(tepDinhHuongPath(id))
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [KEY] })
    },
  })
}

export function dinhHuongLabel(item: DinhHuongRef | null | undefined): string {
  return item ? `${item.ma} — ${item.ten}` : '—'
}
