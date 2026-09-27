import type { AppRoute } from '../../app/registry'
import CohortsPage from './CohortsPage'

export const routes: AppRoute[] = [
  {
    path: '/dot-do-an',
    roles: ['BO_MON'],
    breadcrumb: ['Quản trị', 'Quản lý đợt đồ án'],
    element: <CohortsPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Quản lý đợt đồ án',
      order: 20,
    },
  },
]
