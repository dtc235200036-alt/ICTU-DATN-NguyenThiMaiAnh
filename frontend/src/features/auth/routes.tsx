import type { AppRoute } from '../../app/registry'
import LoginPage from './LoginPage'

export const routes: AppRoute[] = [
  {
    path: '/dang-nhap',
    public: true,
    element: <LoginPage />,
  },
]
