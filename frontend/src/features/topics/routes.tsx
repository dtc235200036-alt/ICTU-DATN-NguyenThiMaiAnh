import { Navigate } from 'react-router'

import type { AppRoute } from '../../app/registry'
import TopicDetailPage from './TopicDetailPage'
import TopicFormPage from './TopicFormPage'

// D-09: '/de-tai/de-xuat' phục vụ cả GV và SV cùng một trang; nhãn menu khác
// nhau theo vai trò (GV "Đề xuất đề tài" / SV "Đề xuất / Đăng ký đề tài") nên
// SV có thêm một mục menu riêng (route ẩn, không bao giờ được điều hướng tới
// trực tiếp — onClick dùng menu.to trỏ thẳng về '/de-tai/de-xuat') vì một
// MenuEntry chỉ mang được một nhãn. Plan 02-05 sẽ đổi menu.to của mục SV sang
// trang danh sách đề tài.
export const routes: AppRoute[] = [
  {
    path: '/de-tai/de-xuat',
    roles: ['SINH_VIEN', 'GIANG_VIEN'],
    breadcrumb: ['Quản lý đề tài', 'Đề xuất đề tài'],
    element: <TopicFormPage />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Đề xuất đề tài',
      order: 30,
    },
  },
  {
    path: '/de-tai/de-xuat-sv-menu',
    roles: ['SINH_VIEN'],
    element: <Navigate to="/de-tai/de-xuat" replace />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Đề xuất / Đăng ký đề tài',
      order: 30,
      to: '/de-tai/de-xuat',
    },
  },
  {
    path: '/de-tai/:id',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Quản lý đề tài', 'Chi tiết đề tài'],
    element: <TopicDetailPage />,
  },
  {
    path: '/de-tai/:id/sua',
    roles: ['SINH_VIEN', 'GIANG_VIEN'],
    breadcrumb: ['Quản lý đề tài', 'Sửa đề tài'],
    element: <TopicFormPage />,
  },
]
