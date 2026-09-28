import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'

// UC0.5/NOTF-01/D-08: mirror app/schemas/notifications.py.
export interface NotificationOut {
  id: number
  loai: string
  noi_dung: string
  lien_ket: string | null
  da_doc: boolean
  thoi_diem: string
}

export interface NotificationPage {
  items: NotificationOut[]
  total: number
  page: number
  page_size: number
  chua_doc: number
}

export interface UnreadCountOut {
  chua_doc: number
}

const NOTIFICATIONS_KEY = ['notifications'] as const

/** D-08: polling 30 s qua TanStack Query (không websocket); dừng khi tab ẩn. */
export function useUnreadCount() {
  return useQuery({
    queryKey: [...NOTIFICATIONS_KEY, 'unread-count'],
    queryFn: async () => (await api.get<UnreadCountOut>('/notifications/unread-count')).data,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  })
}

export function useNotifications(pageSize = 10, enabled = true) {
  return useQuery({
    queryKey: [...NOTIFICATIONS_KEY, 'list', pageSize],
    queryFn: async () =>
      (
        await api.get<NotificationPage>('/notifications', {
          params: { page: 1, page_size: pageSize },
        })
      ).data,
    enabled,
  })
}

export function useMarkRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.post(`/notifications/${id}/read`)
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  })
}

export function useMarkAllRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await api.post('/notifications/read-all')
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  })
}

/** T-03-38: chỉ điều hướng tới đường dẫn nội bộ một dấu "/" (không "//", không scheme). */
export function isAppPath(link: string | null | undefined): link is string {
  return (
    typeof link === 'string' &&
    link.startsWith('/') &&
    !link.startsWith('//') &&
    !link.startsWith('/\\')
  )
}
