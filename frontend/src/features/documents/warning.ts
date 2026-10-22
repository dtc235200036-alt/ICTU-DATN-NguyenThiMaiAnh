import { formatPercent } from '../../utils/format'
import type { CheckSummary } from './api'

type WarningFields = Pick<
  CheckSummary,
  'ly_do_vuot_nguong' | 'ty_le_tong' | 'ty_le_nguon_cao_nhat' | 'nguong_ap_dung' | 'nguong_tong_ap_dung'
>

/** 0017: vì sao Web API kết luận "Vượt ngưỡng cảnh báo" (null khi không vượt). */
export function warningReason(data: WarningFields): string | null {
  if (data.ly_do_vuot_nguong === 'TONG_NGUON') {
    return `Tổng phần trùng với nhiều đồ án ${formatPercent(data.ty_le_tong)} từ ngưỡng tổng ${formatPercent(
      data.nguong_tong_ap_dung,
    )} trở lên`
  }
  if (data.ly_do_vuot_nguong === 'MOT_NGUON') {
    return `Trùng với một đồ án ${formatPercent(data.ty_le_nguon_cao_nhat)} từ ngưỡng ${formatPercent(
      data.nguong_ap_dung,
    )} trở lên`
  }
  return null
}

/** Ngưỡng chụp lúc kiểm tra; kết quả cũ (trước 0017) không có ngưỡng tổng. */
export function thresholdText(data: Pick<CheckSummary, 'nguong_ap_dung' | 'nguong_tong_ap_dung'>): string {
  if (data.nguong_tong_ap_dung === null) return formatPercent(data.nguong_ap_dung)
  return `${formatPercent(data.nguong_ap_dung)} với một đồ án · ${formatPercent(data.nguong_tong_ap_dung)} tổng mọi đồ án`
}
