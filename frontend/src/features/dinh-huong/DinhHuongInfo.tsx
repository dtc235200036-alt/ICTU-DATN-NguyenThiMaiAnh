import { Space } from 'antd'

import { dinhHuongLabel, useDinhHuong } from './api'
import type { DinhHuongRef } from './api'
import TepMoTaButton from './TepMoTaButton'

/**
 * Định hướng của một đề tài ("H01 — Phát triển ứng dụng") kèm nút xem file PDF
 * mô tả khi Bộ môn đã tải lên — tra trong danh mục (useDinhHuong, dùng chung
 * cache), vì DinhHuongRef của đề tài/đề cương không mang thông tin file.
 */
export default function DinhHuongInfo({ value }: { value: DinhHuongRef | null | undefined }) {
  const { data } = useDinhHuong()
  const item = value ? data?.find((d) => d.id === value.id) : undefined
  if (!item?.tep) return <>{dinhHuongLabel(value)}</>
  return (
    <Space size={8} wrap>
      <span>{dinhHuongLabel(value)}</span>
      <TepMoTaButton dinhHuong={item} label="Xem mô tả" />
    </Space>
  )
}
