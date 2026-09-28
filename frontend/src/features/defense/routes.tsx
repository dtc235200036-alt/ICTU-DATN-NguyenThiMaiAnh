import type { AppRoute } from '../../app/registry'
import CommitteePage from './CommitteePage'
import MyDefensePage from './MyDefensePage'
import ScoringPage from './ScoringPage'

// UC4.2/MH-11: Bộ môn lập hội đồng và xếp lịch bảo vệ — GVHD của một SV
// không bao giờ được ngồi hội đồng của chính SV đó (D-06, chặn ở server).
// UC4.3/MH-12: GV chỉ chấm SV trong hội đồng mình là thành viên (403 ở server).
// UC4.5/MH-02: SV xem lịch và — chỉ sau khi chốt — điểm bảo vệ.
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
  {
    path: '/cham-diem',
    roles: ['GIANG_VIEN'],
    breadcrumb: ['Hội đồng bảo vệ', 'Chấm điểm bảo vệ'],
    element: <ScoringPage />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Hội đồng bảo vệ',
      order: 60,
    },
  },
  {
    path: '/bao-ve',
    roles: ['SINH_VIEN'],
    breadcrumb: ['Bảo vệ', 'Lịch và kết quả bảo vệ'],
    element: <MyDefensePage />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Bảo vệ',
      order: 60,
    },
  },
]
