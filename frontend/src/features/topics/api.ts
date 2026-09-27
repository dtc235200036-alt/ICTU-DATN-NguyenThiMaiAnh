import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

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
