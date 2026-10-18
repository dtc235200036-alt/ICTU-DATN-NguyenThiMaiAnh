import type { AppRoute } from '../../app/registry'
import DinhHuongPage from './DinhHuongPage'

export const routes: AppRoute[] = [
  {
    path: '/dinh-huong',
    roles: ['BO_MON'],
    breadcrumb: ['Quản trị', 'Định hướng đề tài'],
    element: <DinhHuongPage />,
    menu: { roles: ['BO_MON'], label: 'Định hướng đề tài', order: 36 },
  },
]
