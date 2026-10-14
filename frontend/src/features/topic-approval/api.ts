import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'
import type { CohortRef, PersonRef } from '../topics/api'

export type TitleCheckSummaryStatus = 'KHONG_TRUNG' | 'CO_TUONG_TU' | 'CHUA_KIEM_TRA'

export interface TitleCheckSummary {
  trang_thai: TitleCheckSummaryStatus
  so_tuong_tu: number
}

export interface PendingTopicItem {
  id: number
  ten_de_tai: string
  linh_vuc: string | null
  dot_do_an: CohortRef
  loai_nguoi_de_xuat: 'GIANG_VIEN' | 'SINH_VIEN'
  nguoi_de_xuat: PersonRef
  sinh_vien: PersonRef | null
  giang_vien: PersonRef | null
  ngay_de_xuat: string | null
  kiem_tra_ten: TitleCheckSummary
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PendingTopicsQueryParams {
  dot_do_an_id?: number
  page?: number
  page_size?: number
}

const PENDING_KEY = 'topic-approvals'
const TOPIC_KEY = 'topics'

// MH-07/UC1.3: đề tài Chờ duyệt của lớp GV gọi (lọc theo đợt nếu chọn).
export function usePendingTopics(params: PendingTopicsQueryParams) {
  return useQuery({
    queryKey: [PENDING_KEY, params],
    queryFn: async () => {
      const { data } = await api.get<PageResult<PendingTopicItem>>('/topic-approvals', { params })
      return data
    },
  })
}

function invalidateApprovalQueries(queryClient: ReturnType<typeof useQueryClient>, id: number) {
  void queryClient.invalidateQueries({ queryKey: [PENDING_KEY] })
  void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY, id] })
  void queryClient.invalidateQueries({ queryKey: [TOPIC_KEY] })
}

// UC1.3: GVHD duyệt đề tài SV trong lớp mình đề xuất -> Đã phân công.
export function useApproveTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/topic-approvals/${id}/approve`)
      return data
    },
    onSuccess: (_data, id) => invalidateApprovalQueries(queryClient, id),
  })
}

export function useRejectTopic() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ly_do }: { id: number; ly_do: string }) => {
      const { data } = await api.post(`/topic-approvals/${id}/reject`, { ly_do })
      return data
    },
    onSuccess: (_data, variables) => invalidateApprovalQueries(queryClient, variables.id),
  })
}
