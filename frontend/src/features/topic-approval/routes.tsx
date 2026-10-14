import type { AppRoute } from '../../app/registry'
import TopicApprovalPage from './TopicApprovalPage'

// D-09/MH-07/UC1.3 (đổi ở 0015): GVHD duyệt đề tài SV trong lớp mình đề xuất —
// RBAC thật do require_role(GIANG_VIEN) + kiểm tra GVHD ở backend quyết định.
export const routes: AppRoute[] = [
  {
    path: '/duyet-de-tai',
    roles: ['GIANG_VIEN'],
    breadcrumb: ['Quản lý đề tài', 'Duyệt đề tài'],
    element: <TopicApprovalPage />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Duyệt đề tài',
      order: 25,
    },
  },
]
