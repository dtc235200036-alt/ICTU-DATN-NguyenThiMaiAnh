import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'

import type { VaiTro } from '../../app/registry'
import { useAuthStore } from '../../stores/auth'
import ForbiddenPage from './ForbiddenPage'

interface RequireAuthProps {
  roles?: VaiTro[]
  children: ReactNode
}

/**
 * D-07/D-09: bởi lúc RequireAuth render, AuthBootstrap đã chặn 'checking' —
 * status ở đây chỉ còn 'authenticated' hoặc 'anonymous'.
 */
export default function RequireAuth({ roles, children }: RequireAuthProps) {
  const location = useLocation()
  const status = useAuthStore((s) => s.status)
  const user = useAuthStore((s) => s.user)

  if (status === 'anonymous' || !user) {
    return <Navigate to="/dang-nhap" state={{ from: location }} replace />
  }

  if (roles && !roles.includes(user.vai_tro)) {
    return <ForbiddenPage />
  }

  return <>{children}</>
}
