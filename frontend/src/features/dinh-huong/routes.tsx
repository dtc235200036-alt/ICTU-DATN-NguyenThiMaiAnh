import type { AppRoute } from '../../app/registry'
import DinhHuongPage from './DinhHuongPage'
import DinhHuongXemPage from './DinhHuongXemPage'

// Bộ môn quản lý danh mục ở '/dinh-huong' (nhóm Quản trị); SV/GV xem danh mục
// cùng file PDF mô tả ở trang chỉ đọc riêng (breadcrumb khác, không có thao tác sửa).
export const routes: AppRoute[] = [
  {
    path: '/dinh-huong',
    roles: ['BO_MON'],
    breadcrumb: ['Quản trị', 'Định hướng đề tài'],
    element: <DinhHuongPage />,
    menu: { roles: ['BO_MON'], label: 'Định hướng đề tài', order: 36 },
  },
  {
    path: '/xem-dinh-huong',
    roles: ['SINH_VIEN', 'GIANG_VIEN'],
    breadcrumb: ['Định hướng đề tài'],
    element: <DinhHuongXemPage />,
    menu: { roles: ['SINH_VIEN', 'GIANG_VIEN'], label: 'Định hướng đề tài', order: 35 },
  },
]
