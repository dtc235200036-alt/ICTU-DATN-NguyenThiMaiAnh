import type { AppRoute } from '../../app/registry'
import OutlinePage from './OutlinePage'
import OutlineReviewPage from './OutlineReviewPage'

// D-09/MH-08/MH-09: '/de-cuong' (SV nộp/xem lịch sử), '/duyet-de-cuong' (GVHD
// duyệt/yêu cầu sửa) — thin tracer screens (full MH-08/09 fidelity: plan 03-02).
export const routes: AppRoute[] = [
  {
    path: '/de-cuong',
    roles: ['SINH_VIEN'],
    breadcrumb: ['Quản lý đề cương', 'Nộp đề cương'],
    element: <OutlinePage />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Nộp đề cương',
      order: 40,
    },
  },
  {
    path: '/duyet-de-cuong',
    roles: ['GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Quản lý đề cương', 'Duyệt đề cương'],
    element: <OutlineReviewPage />,
    menu: {
      // Cùng nhãn/order cho cả hai vai trò (MH-04/11/13) — một MenuEntry đủ,
      // không cần route "shim" như /de-tai (nhãn khác nhau theo vai trò).
      roles: ['GIANG_VIEN', 'BO_MON'],
      label: 'Duyệt đề cương',
      order: 40,
    },
  },
]
