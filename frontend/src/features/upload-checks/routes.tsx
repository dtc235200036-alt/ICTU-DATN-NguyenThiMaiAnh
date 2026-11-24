import type { AppRoute } from '../../app/registry'
import UploadCheckDetailPage from './UploadCheckDetailPage'
import UploadCheckPage from './UploadCheckPage'

export const routes: AppRoute[] = [
  {
    path: '/kiem-tra-dao-van',
    roles: ['GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Kiểm tra đạo văn'],
    element: <UploadCheckPage />,
    menu: { roles: ['GIANG_VIEN', 'BO_MON'], label: 'Kiểm tra đạo văn', order: 75 },
  },
  {
    path: '/kiem-tra-dao-van/:ketQuaId',
    roles: ['GIANG_VIEN', 'BO_MON'],
    breadcrumb: ['Kiểm tra đạo văn', 'Kết quả kiểm tra'],
    element: <UploadCheckDetailPage />,
  },
]
