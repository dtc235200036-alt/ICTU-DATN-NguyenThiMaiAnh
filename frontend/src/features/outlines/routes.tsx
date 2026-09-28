import type { AppRoute } from '../../app/registry'
import OutlinePage from './OutlinePage'
import OutlineReviewPage from './OutlineReviewPage'

// D-09/MH-08/MH-09: '/de-cuong' (SV nộp/xem lịch sử), '/duyet-de-cuong' (GVHD
// duyệt/yêu cầu sửa) — thin tracer screens (full MH-08/09 fidelity: plan 03-02).
export const routes: AppRoute[] = [
  {
    path: '/de-cuong',
    roles: ['SINH_VIEN'],
    breadcrumb: ['Quản lý đề cương', 'Nộp đề cương / báo cáo cuối'],
    element: <OutlinePage />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Đề cương',
      order: 40,
    },
  },
  {
    path: '/duyet-de-cuong',
    roles: ['GIANG_VIEN'],
    breadcrumb: ['Quản lý đề cương', 'Duyệt đề cương'],
    element: <OutlineReviewPage />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Duyệt đề cương',
      order: 40,
    },
  },
]
