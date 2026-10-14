import type { AppRoute } from '../../app/registry'
import AssignmentPage from './AssignmentPage'
import MyStudentsPage from './MyStudentsPage'

// UC0.8: Bộ môn phân công GVHD theo đợt (MH-15); GV xem lớp hướng dẫn của
// mình (MH-16). RBAC thật do require_role ở /api/assignments quyết định.
export const routes: AppRoute[] = [
  {
    path: '/phan-cong-gvhd',
    roles: ['BO_MON'],
    breadcrumb: ['Quản lý đề tài', 'Phân công GVHD'],
    element: <AssignmentPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Phân công GVHD',
      order: 25,
    },
  },
  {
    path: '/sinh-vien-huong-dan',
    roles: ['GIANG_VIEN'],
    breadcrumb: ['Quản lý đề tài', 'Sinh viên của tôi'],
    element: <MyStudentsPage />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Sinh viên của tôi',
      order: 15,
    },
  },
]
