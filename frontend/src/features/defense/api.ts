import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'

import { api } from '../../api/client'
import type { CheckSummary, DocumentOut, PersonRef } from '../documents/api'

// UC4/DEFN-01..02: các kiểu mirror app/schemas/defense.py — báo cáo cuối
// (UC4.1) và hội đồng/lịch bảo vệ (UC4.2, D-06 — GVHD không được ngồi hội
// đồng của chính SV mình hướng dẫn, chặn ở server, đây chỉ hiển thị lại).
export type VaiTroThanhVien = 'CHU_TICH' | 'THU_KY' | 'UY_VIEN'

export interface MemberIn {
  giang_vien_id: number
  vai_tro: VaiTroThanhVien
}

export interface CommitteeIn {
  ten_hoi_dong: string
  ngay_bao_ve: string
  gio_bao_ve: string
  phong: string
  thanh_vien: MemberIn[]
}

export interface MemberOut {
  giang_vien: PersonRef
  hoc_vi: string | null
  vai_tro: VaiTroThanhVien
}

export interface ScheduleRow {
  id: number
  thu_tu: number | null
  gio_du_kien: string
  sinh_vien: PersonRef
  de_tai_id: number
  ten_de_tai: string
  giang_vien_huong_dan: PersonRef | null
  so_da_cham: number
  so_thanh_vien: number
  diem_tam_tinh: number | null
  diem_trung_binh: number | null
  da_chot: boolean
  bao_cao_cuoi: DocumentOut | null
  kiem_tra: CheckSummary | null
}

export interface CommitteeOut {
  id: number
  ten_hoi_dong: string
  ngay_bao_ve: string
  gio_bao_ve: string
  phong: string
  thanh_vien: MemberOut[]
  lich: ScheduleRow[]
}

export interface CommitteeListItem {
  id: number
  ten_hoi_dong: string
  ngay_bao_ve: string
  gio_bao_ve: string
  phong: string
  chu_tich: PersonRef | null
  so_thanh_vien: number
  so_sinh_vien: number
}

export interface EligibleStudent {
  de_tai_id: number
  ten_de_tai: string
  sinh_vien: PersonRef
  giang_vien_huong_dan: PersonRef | null
  giang_vien_id: number | null
  bao_cao_cuoi: DocumentOut
  kiem_tra: CheckSummary | null
}

export interface FinalReportVersion {
  tai_lieu: DocumentOut
  kiem_tra: CheckSummary | null
}

export interface FinalReportDetail {
  de_tai_id: number
  ten_de_tai: string
  trang_thai_de_cuong: string
  da_xep_lich: boolean
  phien_ban: FinalReportVersion[]
  quyen: { nop: boolean }
}

const DEFENSE_KEY = 'defense'

function hasPendingCheck(detail: FinalReportDetail | undefined): boolean {
  if (!detail) return false
  return detail.phien_ban.some((version) => version.kiem_tra?.trang_thai === 'DANG_KIEM_TRA')
}

function noRetryOn4xx(failureCount: number, error: unknown): boolean {
  const status = error instanceof AxiosError ? error.response?.status : undefined
  if (status !== undefined && status < 500) return false
  return failureCount < 3
}

// D-04/UC4.1: poll mỗi 3s trong khi phiên bản mới nhất còn Đang kiểm tra;
// không chặn Bộ môn lập hội đồng trong lúc đó (UC4.1 - E2).
export function useFinalReport(deTaiId: number | undefined) {
  return useQuery({
    queryKey: [DEFENSE_KEY, 'final-report', deTaiId],
    queryFn: async () => {
      const { data } = await api.get<FinalReportDetail>(`/defense/final-reports/${deTaiId}`)
      return data
    },
    enabled: deTaiId !== undefined,
    refetchInterval: (query) => (hasPendingCheck(query.state.data) ? 3000 : false),
    retry: noRetryOn4xx,
  })
}

export function useSubmitFinalReport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ deTaiId, file }: { deTaiId: number; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post<FinalReportDetail>(`/defense/final-reports/${deTaiId}`, formData)
      return data
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: [DEFENSE_KEY, 'final-report', variables.deTaiId],
      })
      void queryClient.invalidateQueries({ queryKey: [DEFENSE_KEY, 'eligible-students'] })
    },
  })
}

export function useCommittees() {
  return useQuery({
    queryKey: [DEFENSE_KEY, 'committees'],
    queryFn: async () => {
      const { data } = await api.get<CommitteeListItem[]>('/defense/committees')
      return data
    },
    placeholderData: keepPreviousData,
  })
}

export function useCommittee(id: number | undefined) {
  return useQuery({
    queryKey: [DEFENSE_KEY, 'committees', id],
    queryFn: async () => {
      const { data } = await api.get<CommitteeOut>(`/defense/committees/${id}`)
      return data
    },
    enabled: id !== undefined,
  })
}

export function useEligibleStudents() {
  return useQuery({
    queryKey: [DEFENSE_KEY, 'eligible-students'],
    queryFn: async () => {
      const { data } = await api.get<EligibleStudent[]>('/defense/eligible-students')
      return data
    },
  })
}

function invalidateCommitteeQueries(queryClient: QueryClient, id?: number) {
  void queryClient.invalidateQueries({ queryKey: [DEFENSE_KEY, 'committees'] })
  void queryClient.invalidateQueries({ queryKey: [DEFENSE_KEY, 'eligible-students'] })
  if (id !== undefined) {
    void queryClient.invalidateQueries({ queryKey: [DEFENSE_KEY, 'committees', id] })
  }
}

// POST khi tạo mới (id undefined), PUT khi sửa hội đồng đã có (D-09/MH-11:
// một Form dùng chung cho cả hai chế độ "moi"/đã chọn).
export function useSaveCommittee() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, input }: { id?: number; input: CommitteeIn }) => {
      const { data } =
        id !== undefined
          ? await api.put<CommitteeOut>(`/defense/committees/${id}`, input)
          : await api.post<CommitteeOut>('/defense/committees', input)
      return data
    },
    onSuccess: (data) => {
      invalidateCommitteeQueries(queryClient, data.id)
    },
  })
}

export function useDeleteCommittee() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/defense/committees/${id}`)
    },
    onSuccess: () => {
      invalidateCommitteeQueries(queryClient)
    },
  })
}

export function useAddSchedule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ hoiDongId, deTaiId }: { hoiDongId: number; deTaiId: number }) => {
      const { data } = await api.post<ScheduleRow>(`/defense/committees/${hoiDongId}/schedules`, {
        de_tai_id: deTaiId,
      })
      return data
    },
    onSuccess: (_data, variables) => {
      invalidateCommitteeQueries(queryClient, variables.hoiDongId)
    },
  })
}

export function useRemoveSchedule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ hoiDongId, lichBaoVeId }: { hoiDongId: number; lichBaoVeId: number }) => {
      await api.delete(`/defense/schedules/${lichBaoVeId}`)
      return hoiDongId
    },
    onSuccess: (hoiDongId) => {
      invalidateCommitteeQueries(queryClient, hoiDongId)
    },
  })
}
