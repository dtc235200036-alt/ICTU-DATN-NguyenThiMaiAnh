import type { AppRoute } from '../../app/registry'
import ProgressOverviewPage from './ProgressOverviewPage'
import ProgressPage from './ProgressPage'
import ProgressReviewPage from './ProgressReviewPage'

// UC3: SV nộp báo cáo theo mốc (MH-10), GVHD nhận xét (MH-10), Bộ môn đặt
// mốc + theo dõi toàn khoa (MH-04) — quyền thật chặn ở server (require_role).
export const routes: AppRoute[] = [
  {
    path: '/tien-do',
    roles: ['SINH_VIEN'],
    breadcrumb: ['Quản lý tiến độ', 'Báo cáo tiến độ'],
    element: <ProgressPage />,
    menu: { roles: ['SINH_VIEN'], label: 'Báo cáo tiến độ', order: 50 },
  },
  {
    path: '/nhan-xet-tien-do',
    roles: ['GIANG_VIEN'],
    breadcrumb: ['Quản lý tiến độ', 'Nhận xét tiến độ'],
    element: <ProgressReviewPage />,
    menu: { roles: ['GIANG_VIEN'], label: 'Nhận xét tiến độ', order: 50 },
  },
  {
    path: '/tien-do-toan-khoa',
    roles: ['BO_MON'],
    breadcrumb: ['Quản lý tiến độ', 'Tiến độ toàn khoa'],
    element: <ProgressOverviewPage />,
    menu: { roles: ['BO_MON'], label: 'Tiến độ toàn khoa', order: 50 },
  },
]
