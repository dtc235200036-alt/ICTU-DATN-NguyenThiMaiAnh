import type { AppRoute } from '../../app/registry'
import CommitteePage from './CommitteePage'

// UC4.2/MH-11: Bộ môn lập hội đồng và xếp lịch bảo vệ — GVHD của một SV
// không bao giờ được ngồi hội đồng của chính SV đó (D-06, chặn ở server).
export const routes: AppRoute[] = [
  {
    path: '/hoi-dong',
    roles: ['BO_MON'],
    breadcrumb: ['Quản lý bảo vệ', 'Hội đồng & lịch bảo vệ'],
    element: <CommitteePage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Hội đồng & lịch bảo vệ',
      order: 60,
    },
  },
]
