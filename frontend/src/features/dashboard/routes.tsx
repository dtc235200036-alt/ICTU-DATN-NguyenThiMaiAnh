import { Navigate } from 'react-router'
import type { AppRoute } from '../../app/registry'
import DashboardPage from './DashboardPage'
import SubmissionHistoryPage from './SubmissionHistoryPage'

export const routes: AppRoute[] = [
  {
    path: '/tong-quan',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Tổng quan'],
    element: <DashboardPage />,
    menu: {
      roles: ['GIANG_VIEN', 'BO_MON'],
      label: 'Tổng quan',
      order: 10,
    },
  },
  {
    // SV: cùng trang tổng quan nhưng nhãn "Trang chủ" (route shim, xem topics/routes.tsx).
    path: '/trang-chu',
    roles: ['SINH_VIEN'],
    element: <Navigate to="/tong-quan" replace />,
    menu: { roles: ['SINH_VIEN'], label: 'Trang chủ', order: 10, to: '/tong-quan' },
  },
  {
    path: '/lich-su-nop',
    roles: ['SINH_VIEN'],
    breadcrumb: ['Lịch sử nộp'],
    element: <SubmissionHistoryPage />,
    menu: { roles: ['SINH_VIEN'], label: 'Lịch sử nộp', order: 55 },
  },
]
