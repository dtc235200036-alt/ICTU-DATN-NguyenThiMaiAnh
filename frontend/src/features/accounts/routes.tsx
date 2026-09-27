import type { AppRoute } from '../../app/registry'
import AccountsPage from './AccountsPage'

export const routes: AppRoute[] = [
  {
    path: '/tai-khoan',
    roles: ['BO_MON'],
    breadcrumb: ['Quản trị', 'Quản lý tài khoản'],
    element: <AccountsPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Quản lý tài khoản',
      order: 90,
    },
  },
]
