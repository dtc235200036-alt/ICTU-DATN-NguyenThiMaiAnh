import type { OutlineTrangThai } from './api'

/** Nhãn + màu trạng thái đề cương — một nơi dùng chung cho SV/GV/Bộ môn. */
export const TRANG_THAI_DE_CUONG: Record<OutlineTrangThai, { label: string; color: string }> = {
  CHUA_NOP: { label: 'Chưa nộp', color: 'default' },
  CHO_DUYET: { label: 'Chờ GVHD duyệt', color: 'processing' },
  YEU_CAU_SUA: { label: 'Yêu cầu sửa', color: 'error' },
  GVHD_DA_DUYET: { label: 'GVHD đã duyệt', color: 'cyan' },
  CHO_BO_MON_DUYET: { label: 'Chờ Bộ môn duyệt', color: 'gold' },
  DA_DUYET: { label: 'Đã duyệt', color: 'success' },
}

export function trangThaiDeCuong(value: string): { label: string; color: string } {
  return TRANG_THAI_DE_CUONG[value as OutlineTrangThai] ?? { label: value, color: 'default' }
}

/** Kiểm tra phía trình duyệt: tên file <Hxx>.<MSSV>.<Họ tên>.<Lớp>.<pdf|docx>. */
export function tenFileHopLe(name: string): boolean {
  const normalized = name.normalize('NFC').trim()
  const dot = normalized.lastIndexOf('.')
  if (dot < 0) return false
  const ext = normalized.slice(dot + 1).toLowerCase()
  if (ext !== 'pdf' && ext !== 'docx') return false
  const parts = normalized.slice(0, dot).split('.').map((p) => p.trim())
  return parts.length === 4 && parts.every(Boolean) && /^H\d{2}$/i.test(parts[0])
}
