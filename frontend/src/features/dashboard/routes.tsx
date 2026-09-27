import type { AppRoute } from '../../app/registry'
import DashboardPage from './DashboardPage'

export const routes: AppRoute[] = [
  {
    path: '/tong-quan',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Tổng quan'],
    element: <DashboardPage />,
    menu: {
      roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
      label: 'Tổng quan',
      order: 10,
    },
  },
]
