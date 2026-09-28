import { Tag } from 'antd'

import { formatPercent } from '../../utils/format'
import type { CheckStatus, CheckSummary } from './api'

export interface CheckStatusTagProps {
  kiemTra: Pick<CheckSummary, 'trang_thai' | 'ty_le_tong'> | null | undefined
}

const STATUS_LABEL: Record<CheckStatus, string> = {
  HOAN_TAT: 'Hoàn tất',
  DANG_KIEM_TRA: 'Đang kiểm tra',
  LOI: 'Lỗi',
}

/** UC0.7: Tag trạng thái kiểm tra trùng lặp dùng chung ở mọi bảng/màn hình. */
export default function CheckStatusTag({ kiemTra }: CheckStatusTagProps) {
  if (!kiemTra) {
    return <Tag>Chưa kiểm tra</Tag>
  }
  if (kiemTra.trang_thai === 'HOAN_TAT') {
    return <Tag color="success">{`${STATUS_LABEL.HOAN_TAT} - ${formatPercent(kiemTra.ty_le_tong)}`}</Tag>
  }
  if (kiemTra.trang_thai === 'DANG_KIEM_TRA') {
    return <Tag color="processing">{STATUS_LABEL.DANG_KIEM_TRA}</Tag>
  }
  return <Tag color="error">{STATUS_LABEL.LOI}</Tag>
}
