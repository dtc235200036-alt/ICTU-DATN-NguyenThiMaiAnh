import type { AppRoute } from '../../app/registry'
import ArchivePage from './ArchivePage'

// UC5.1/MH-13: mọi vai trò tra cứu kho đồ án và tải báo cáo cuối đã lưu kho;
// UC5.3/UC5.4: chỉ Bộ môn thêm/sửa/xóa/index lại/import (403 ở server).
export const routes: AppRoute[] = [
  {
    path: '/kho-do-an',
    roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Kho đồ án'],
    element: <ArchivePage />,
    menu: {
      roles: ['SINH_VIEN', 'GIANG_VIEN', 'BO_MON'],
      label: 'Kho đồ án',
      order: 70,
    },
  },
]
