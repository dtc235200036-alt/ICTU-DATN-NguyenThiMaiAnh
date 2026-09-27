// §3.4.7: 5 trạng thái đề tài (FR-DT-07) — nhãn + màu Tag dùng ở MH-05/06/07.
export const TRANG_THAI_DE_TAI: Record<string, { label: string; color: string }> = {
  NHAP: { label: 'Nháp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  DA_DUYET: { label: 'Đã duyệt', color: 'warning' },
  TU_CHOI: { label: 'Từ chối', color: 'error' },
  DA_PHAN_CONG: { label: 'Đã phân công', color: 'success' },
}

// D-04: lĩnh vực đề tài — danh sách cố định cho MH-06 (Select).
export const LINH_VUC_OPTIONS = [
  'Trí tuệ nhân tạo & Xử lý ngôn ngữ tự nhiên',
  'Hệ thống thông tin',
  'Mạng máy tính & An toàn thông tin',
  'Công nghệ phần mềm',
  'IoT & Hệ thống nhúng',
  'Khoa học dữ liệu',
]
