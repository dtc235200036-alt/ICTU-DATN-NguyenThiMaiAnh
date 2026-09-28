import type { AppRoute } from '../../app/registry'
import CheckDetailPage from './CheckDetailPage'

// MH-14/D-04: mở từ CheckPanel ("Xem chi tiết") và từ Tag "Hoàn tất - N%" ở
// lịch sử phiên bản (MH-08). Mọi vai trò có quyền xem tài liệu đều truy cập
// được — không có mục menu riêng (documents.get_viewable_or_error tự giới
// hạn theo quyền ở tầng API).
export const routes: AppRoute[] = [
  {
    path: '/kiem-tra-trung-lap/:taiLieuId',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Kiểm tra trùng lặp', 'Chi tiết kết quả kiểm tra trùng lặp'],
    element: <CheckDetailPage />,
  },
]
