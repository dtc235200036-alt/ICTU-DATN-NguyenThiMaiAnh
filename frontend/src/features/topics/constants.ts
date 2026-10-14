// §3.4.7 (FR-DT-07): nhãn + màu Tag dùng ở MH-05/06/07. Góp ý GVHD mục 1: hệ
// thống chỉ còn hai trạng thái Nháp -> Đã phân công; ba trạng thái cũ giữ trong
// bảng nhãn để hàng dữ liệu cũ vẫn hiển thị đúng (không còn được tạo ra).
export const TRANG_THAI_DE_TAI: Record<string, { label: string; color: string }> = {
  NHAP: { label: 'Nháp', color: 'default' },
  CHO_DUYET: { label: 'Chờ duyệt', color: 'processing' },
  DA_DUYET: { label: 'Đã duyệt', color: 'warning' },
  TU_CHOI: { label: 'Từ chối', color: 'error' },
  DA_PHAN_CONG: { label: 'Đã phân công', color: 'success' },
}

/** Bộ lọc trạng thái ở MH-05: chỉ hai trạng thái hệ thống còn tạo ra. */
export const TRANG_THAI_LOC_OPTIONS = ['NHAP', 'DA_PHAN_CONG'].map((value) => ({
  value,
  label: TRANG_THAI_DE_TAI[value].label,
}))

// D-04: lĩnh vực đề tài — danh sách cố định cho MH-06 (Select).
export const LINH_VUC_OPTIONS = [
  'Trí tuệ nhân tạo & Xử lý ngôn ngữ tự nhiên',
  'Hệ thống thông tin',
  'Mạng máy tính & An toàn thông tin',
  'Công nghệ phần mềm',
  'IoT & Hệ thống nhúng',
  'Khoa học dữ liệu',
]
