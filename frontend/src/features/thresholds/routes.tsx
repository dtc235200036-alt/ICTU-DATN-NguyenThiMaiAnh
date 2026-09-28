import type { AppRoute } from '../../app/registry'
import ThresholdSettingsPage from './ThresholdSettingsPage'

export const routes: AppRoute[] = [
  {
    path: '/cau-hinh-nguong',
    roles: ['BO_MON'],
    breadcrumb: ['Cấu hình', 'Ngưỡng cảnh báo trùng lặp'],
    element: <ThresholdSettingsPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Ngưỡng trùng lặp',
      order: 80,
    },
  },
]
