import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'

export type ThresholdKey = 'NGUONG_TEN_DE_TAI' | 'NGUONG_TAI_LIEU' | 'NGUONG_DOAN_TRUNG'

export interface ThresholdOut {
  loai: ThresholdKey
  nhan: string
  mo_ta: string
  gia_tri: number
  gia_tri_de_xuat: number
  thoi_diem_cap_nhat: string
  nguoi_cap_nhat: string | null
}

export type ThresholdUpdate = Record<ThresholdKey, number>

const THRESHOLDS_KEY = 'thresholds'

// UC0.4/AISV-07: chỉ Bộ môn — 403 là kết quả cuối, không retry trên 4xx.
export function useThresholds() {
  return useQuery({
    queryKey: [THRESHOLDS_KEY],
    queryFn: async () => {
      const { data } = await api.get<ThresholdOut[]>('/thresholds')
      return data
    },
    retry: (failureCount, error) => {
      const status = error instanceof AxiosError ? error.response?.status : undefined
      if (status !== undefined && status < 500) {
        return false
      }
      return failureCount < 3
    },
  })
}

export function useSaveThresholds() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: ThresholdUpdate) => {
      const { data } = await api.put<ThresholdOut[]>('/thresholds', input)
      return data
    },
    onSuccess: (data) => {
      queryClient.setQueryData([THRESHOLDS_KEY], data)
      void queryClient.invalidateQueries({ queryKey: [THRESHOLDS_KEY] })
    },
  })
}
