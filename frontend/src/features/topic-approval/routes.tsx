import type { AppRoute } from '../../app/registry'
import TopicApprovalPage from './TopicApprovalPage'

// D-09/MH-07/UC1.3: chỉ Bộ môn được vào — RBAC thật do
// require_role(BO_MON) ở backend quyết định, route roles chỉ ẩn/hiện menu.
export const routes: AppRoute[] = [
  {
    path: '/duyet-de-tai',
    roles: ['BO_MON'],
    breadcrumb: ['Quản lý đề tài', 'Duyệt & phân công đề tài'],
    element: <TopicApprovalPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Duyệt & phân công đề tài',
      order: 30,
    },
  },
]
