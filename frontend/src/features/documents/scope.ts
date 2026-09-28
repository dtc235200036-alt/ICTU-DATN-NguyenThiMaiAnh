import { formatPercent } from '../../utils/format'
import type { CheckSummary } from './api'

/** CR-04: phạm vi thực sự được kiểm tra (AI thật; bộ giả lập không có). */
export function scopeText(
  data: Pick<CheckSummary, 'so_doan' | 'so_doan_loai_tru' | 'ty_le_loai_tru'>,
): string | null {
  if (data.so_doan === null) return null
  const loaiTru =
    data.so_doan_loai_tru !== null
      ? ` · đã loại ${data.so_doan_loai_tru} dòng phần mẫu chung (${formatPercent(data.ty_le_loai_tru)} nội dung)`
      : ''
  return `Đã so sánh ${data.so_doan} câu${loaiTru}`
}
