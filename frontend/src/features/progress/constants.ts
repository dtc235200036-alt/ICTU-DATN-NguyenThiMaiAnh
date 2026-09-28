// UC3/D-05: trạng thái mốc được server tính từ ngày (không lưu DB) — đây chỉ
// là nhãn/màu hiển thị. UC3.3: ba mức đánh giá của GVHD.
export type TrangThaiMoc = 'DUNG_HAN' | 'NOP_TRE' | 'TRE_MOC' | 'CHUA_DEN_HAN'
export type DanhGia = 'DAT' | 'CAN_CAI_THIEN' | 'CHUA_DAT'

export const TRANG_THAI_MOC: Record<TrangThaiMoc, { label: string; color: string }> = {
  DUNG_HAN: { label: 'Đúng hạn', color: 'green' },
  NOP_TRE: { label: 'Nộp trễ', color: 'orange' },
  TRE_MOC: { label: 'Trễ mốc', color: 'red' },
  CHUA_DEN_HAN: { label: 'Chưa đến hạn', color: 'default' },
}

export const DANH_GIA: Record<DanhGia, { label: string; color: string }> = {
  DAT: { label: 'Đạt', color: 'green' },
  CAN_CAI_THIEN: { label: 'Cần cải thiện', color: 'gold' },
  CHUA_DAT: { label: 'Chưa đạt', color: 'red' },
}

export const DANH_GIA_OPTIONS: { value: DanhGia; label: string }[] = [
  { value: 'DAT', label: 'Đạt' },
  { value: 'CAN_CAI_THIEN', label: 'Cần cải thiện' },
  { value: 'CHUA_DAT', label: 'Chưa đạt' },
]

/** "2026-11-20" (DATE từ server) → "20/11/2026" — không qua Date để tránh lệch múi giờ. */
export function formatDay(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}
