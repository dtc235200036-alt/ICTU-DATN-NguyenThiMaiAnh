import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../../api/client'
import type { DocumentOut } from '../documents/api'
import type { PersonRef } from '../topics/api'

// Mirror backend/app/schemas/archive.py (UC5.1/UC5.3/UC5.4, MH-13).

export type TrangThaiIndex = 'CHUA_INDEX' | 'DA_INDEX'
export type NguonKho = 'HE_THONG' | 'IMPORT'

export interface ArchiveStudent {
  ma: string | null
  ho_ten: string | null
}

export interface ArchiveListItem {
  id: number
  ten_de_tai: string
  khoa: string | null
  sinh_vien: ArchiveStudent | null
  giang_vien: PersonRef | null
  diem: number | null
  tu_khoa: string | null
  nguon: NguonKho
  trang_thai_index: TrangThaiIndex
  co_file: boolean
}

export interface ArchiveDetail extends ArchiveListItem {
  de_tai_id: number | null
  sinh_vien_id: number | null
  file: DocumentOut | null
}

export interface ArchiveIn {
  khoa: string
  ten_de_tai: string
  ma_so_sinh_vien?: string | null
  ho_ten_sinh_vien?: string | null
  giang_vien_id?: number | null
  tu_khoa?: string | null
  diem?: number | null
}

export interface ImportRowError {
  dong: number
  ly_do: string
}

export interface ImportResult {
  tong_dong: number
  thanh_cong: number
  loi: ImportRowError[]
}

export interface ArchivePage {
  items: ArchiveListItem[]
  total: number
  page: number
  page_size: number
}

export interface ArchiveQueryParams {
  khoa?: string
  giang_vien_id?: number
  q?: string
  page: number
  page_size: number
}

const ARCHIVE_KEY = 'archive'

// placeholderData giữ trang cũ khi đổi bộ lọc/trang để tránh flash rỗng.
export function useArchive(params: ArchiveQueryParams) {
  return useQuery({
    queryKey: [ARCHIVE_KEY, 'list', params],
    queryFn: async () => {
      const { data } = await api.get<ArchivePage>('/archive', { params })
      return data
    },
    placeholderData: keepPreviousData,
  })
}

export function useArchiveKhoa() {
  return useQuery({
    queryKey: [ARCHIVE_KEY, 'khoa'],
    queryFn: async () => {
      const { data } = await api.get<string[]>('/archive/khoa')
      return data
    },
  })
}

export function useArchiveRecord(id: number | undefined) {
  return useQuery({
    queryKey: [ARCHIVE_KEY, 'detail', id],
    queryFn: async () => {
      const { data } = await api.get<ArchiveDetail>(`/archive/${id}`)
      return data
    },
    enabled: id !== undefined,
    // Index AI chạy nền sau commit: khi Drawer đang mở một bản ghi "Chưa
    // index", hỏi lại vài giây một lần để thấy "Đã index" không cần tải lại.
    refetchInterval: (query) =>
      query.state.data?.trang_thai_index === 'CHUA_INDEX' ? 3000 : false,
  })
}

// Ghi xong -> làm mới ngay, rồi làm mới thêm một lần sau khi job index AI
// chạy nền (BackgroundTasks sau commit) để cột "Chỉ mục AI" lên "Đã index".
const INDEX_SETTLE_MS = 2000

function useInvalidateArchive() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: [ARCHIVE_KEY] })
    window.setTimeout(() => {
      void queryClient.invalidateQueries({ queryKey: [ARCHIVE_KEY] })
    }, INDEX_SETTLE_MS)
  }
}

export function useCreateArchive() {
  const invalidate = useInvalidateArchive()
  return useMutation({
    mutationFn: async (payload: ArchiveIn) => {
      const { data } = await api.post<ArchiveDetail>('/archive', payload)
      return data
    },
    onSuccess: () => void invalidate(),
  })
}

export function useUpdateArchive() {
  const invalidate = useInvalidateArchive()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: ArchiveIn }) => {
      const { data } = await api.put<ArchiveDetail>(`/archive/${id}`, payload)
      return data
    },
    onSuccess: () => void invalidate(),
  })
}

export function useDeleteArchive() {
  const invalidate = useInvalidateArchive()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/archive/${id}`)
    },
    onSuccess: () => void invalidate(),
  })
}

export function useReindexArchive() {
  const invalidate = useInvalidateArchive()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<ArchiveDetail>(`/archive/${id}/reindex`)
      return data
    },
    onSuccess: () => void invalidate(),
  })
}

export function useImportArchive() {
  const invalidate = useInvalidateArchive()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post<ImportResult>('/archive/import', form)
      return data
    },
    onSuccess: () => void invalidate(),
  })
}
