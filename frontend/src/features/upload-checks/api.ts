import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'
import type { CheckSummary } from '../documents/api'
import type { CheckResultData } from '../documents/CheckDetailPage'

// 0020: GV/Bộ môn tải một tệp lên để kiểm tra trùng lặp với kho (chạy nền như
// kiểm tra tài liệu; tệp không được lưu, không vào chỉ mục).
export interface UploadCheckSummary extends CheckSummary {
  ten_tep: string
}

export type UploadCheckDetail = UploadCheckSummary & CheckResultData

const KEY = 'upload-checks'

export function useUploadChecks() {
  return useQuery({
    queryKey: [KEY],
    queryFn: async () => (await api.get<UploadCheckSummary[]>('/upload-checks')).data,
    refetchInterval: (query) =>
      query.state.data?.some((k) => k.trang_thai === 'DANG_KIEM_TRA') ? 3000 : false,
  })
}

export function useUploadCheck(id: number) {
  return useQuery({
    queryKey: [KEY, id],
    queryFn: async () => (await api.get<UploadCheckDetail>(`/upload-checks/${id}`)).data,
    refetchInterval: (query) => (query.state.data?.trang_thai === 'DANG_KIEM_TRA' ? 3000 : false),
    retry: false,
  })
}

export function useCreateUploadCheck() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return (await api.post<UploadCheckSummary>('/upload-checks', formData)).data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [KEY] })
    },
  })
}
