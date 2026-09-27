import { Navigate } from 'react-router'

import type { AppRoute } from '../../app/registry'
import TopicDetailPage from './TopicDetailPage'
import TopicFormPage from './TopicFormPage'
import TopicListPage from './TopicListPage'

// D-09/MH-05: '/de-tai' là trang danh sách (mọi vai trò); '/de-tai/de-xuat'
// phục vụ cả GV và SV cùng một trang đề xuất. Mỗi vai trò cần nhãn menu khác
// nhau trỏ tới cùng một path — MenuEntry chỉ mang được một nhãn/route, nên
// mỗi nhãn thêm dùng một route "shim" (path riêng, không bao giờ được điều
// hướng tới trực tiếp) mà onClick dùng menu.to trỏ thẳng về path thật.
export const routes: AppRoute[] = [
  {
    path: '/de-tai',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Quản lý đề tài', 'Danh sách đề tài'],
    element: <TopicListPage />,
    menu: {
      roles: ['BO_MON'],
      label: 'Danh sách đề tài',
      order: 35,
    },
  },
  {
    path: '/de-tai/cua-toi-sv-menu',
    roles: ['SINH_VIEN'],
    element: <Navigate to="/de-tai?pham_vi=cua_toi" replace />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Đề tài của tôi',
      order: 20,
      to: '/de-tai?pham_vi=cua_toi',
    },
  },
  {
    path: '/de-tai/cua-toi-gv-menu',
    roles: ['GIANG_VIEN'],
    element: <Navigate to="/de-tai?pham_vi=cua_toi" replace />,
    menu: {
      roles: ['GIANG_VIEN'],
      label: 'Đề tài hướng dẫn',
      order: 20,
      to: '/de-tai?pham_vi=cua_toi',
    },
  },
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
    element: <Navigate to="/de-tai" replace />,
    menu: {
      roles: ['SINH_VIEN'],
      label: 'Đề xuất / Đăng ký đề tài',
      order: 30,
      to: '/de-tai',
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
