import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import type { PersonRef } from '../topics/api'

export type { PersonRef }

// D-04/UC0.7: các kiểu chung cho tài liệu + kết quả kiểm tra trùng lặp — dùng
// bởi đề cương (03-02), báo cáo tiến độ (03-03) và báo cáo cuối/chấm điểm
// (03-04/03-06). Đây là nơi DUY NHẤT khai báo các kiểu này (outlines/api.ts
// import lại từ đây, không tự định nghĩa song song).
export interface DocumentOut {
  id: number
  loai: string
  so_phien_ban: number
  ten_goc: string
  kich_thuoc: number
  dinh_dang: 'DOCX' | 'PDF'
  thoi_diem_nop: string
  trich_xuat_loi: boolean
  tom_tat: string | null
}

export type CheckStatus = 'DANG_KIEM_TRA' | 'HOAN_TAT' | 'LOI'

export interface CheckSummary {
  id: number
  trang_thai: CheckStatus
  /** Chỉ để hiển thị: tỷ lệ câu bị gắn cờ trên toàn tài liệu (mọi nguồn cộng lại) */
  ty_le_tong: number | null
  /** CR-01: tỷ lệ trùng với MỘT đồ án nguồn cao nhất — thống kê được hiệu chỉnh */
  ty_le_nguon_cao_nhat: number | null
  /** CR-01: Web API quyết định (ty_le_nguon_cao_nhat >= nguong_ap_dung); null khi chưa hoàn tất */
  vuot_nguong: boolean | null
  nguong_ap_dung: number
  thoi_diem: string
  /** CR-04: số câu được so sánh (null với bộ giả lập / kết quả cũ) */
  so_doan: number | null
  /** CR-04: số dòng bị loại như phần mẫu chung */
  so_doan_loai_tru: number | null
  /** CR-04: % ký tự bị loại như phần mẫu chung (không được kiểm tra) */
  ty_le_loai_tru: number | null
  /** CR-04: hơn một nửa văn bản bị loại — GVHD nên xem trực tiếp tài liệu */
  loai_tru_nhieu: boolean
}

export interface CheckMatch {
  doi_tuong_trung: string
  ty_le: number
}

export interface CheckSegment {
  doi_tuong_trung: string
  doan_nguon: string | null
  doan_trung: string | null
  vi_tri: string | null
  ty_le: number
  /** WR-07: nguồn là tài liệu chưa công bố của SV khác — SV không xem được đoạn nguồn */
  doan_trung_an: boolean
}

export interface CheckDetail extends CheckSummary {
  tai_lieu: DocumentOut
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef | null
  do_an_trung: CheckMatch[]
  chi_tiet: CheckSegment[]
}

const DOCUMENT_KEY = 'documents'

// D-04: poll mỗi 3s trong khi còn DANG_KIEM_TRA; không retry trên 4xx (404 —
// chưa nộp lần kiểm tra nào — là kết quả cuối, không phải lỗi mạng tạm thời).
export function useDocumentCheck(taiLieuId: number | undefined) {
  return useQuery({
    queryKey: [DOCUMENT_KEY, taiLieuId, 'check'],
    queryFn: async () => {
      const { data } = await api.get<CheckDetail>(`/documents/${taiLieuId}/check`)
      return data
    },
    enabled: taiLieuId !== undefined,
    refetchInterval: (query) => (query.state.data?.trang_thai === 'DANG_KIEM_TRA' ? 3000 : false),
    retry: (failureCount, error) => {
      const status = error instanceof AxiosError ? error.response?.status : undefined
      if (status !== undefined && status < 500) {
        return false
      }
      return failureCount < 3
    },
  })
}

// UC0.7: chỉ gọi được khi kết quả đang ở LOI (server tự chặn bằng conditional
// UPDATE) — invalidate cả check lẫn danh sách/chi tiết đề cương để mọi màn
// hình đang hiển thị Tag trạng thái cập nhật theo.
export function useRecheck() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taiLieuId: number) => {
      const { data } = await api.post<CheckSummary>(`/documents/${taiLieuId}/recheck`)
      return data
    },
    onSuccess: (_data, taiLieuId) => {
      void queryClient.invalidateQueries({ queryKey: [DOCUMENT_KEY, taiLieuId] })
      void queryClient.invalidateQueries({ queryKey: ['outlines'] })
      // WR-13: báo cáo cuối hiển thị trạng thái kiểm tra trong các truy vấn
      // của feature defense (lịch hội đồng, màn chấm điểm, tab báo cáo cuối).
      void queryClient.invalidateQueries({ queryKey: ['defense'] })
    },
  })
}
