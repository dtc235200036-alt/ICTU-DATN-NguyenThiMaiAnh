import { lazy, Suspense } from 'react'
import { Navigate } from 'react-router'

import type { AppRoute } from '../../app/registry'
import { useAuthStore } from '../../stores/auth'

// Tải riêng (gsap + font) để không làm nặng bundle của phần ứng dụng.
const LandingPage = lazy(() => import('./LandingPage'))

/** "/": khách xem trang giới thiệu; đã đăng nhập thì vào thẳng tổng quan. */
function LandingRoute() {
  const status = useAuthStore((s) => s.status)
  if (status === 'authenticated') {
    return <Navigate to="/tong-quan" replace />
  }
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', background: '#060d1f' }} />}>
      <LandingPage />
    </Suspense>
  )
}

export const routes: AppRoute[] = [
  {
    path: '/',
    public: true,
    element: <LandingRoute />,
  },
]
