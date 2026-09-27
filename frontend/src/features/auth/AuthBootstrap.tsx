import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { Spin } from 'antd'

import { refreshSession } from '../../api/client'
import { useAuthStore } from '../../stores/auth'

interface AuthBootstrapProps {
  children: ReactNode
}

/**
 * D-07/AUTH-02: khôi phục phiên đăng nhập khi tải lại trang bằng cách gọi
 * POST /auth/refresh (cookie httpOnly) đúng một lần khi mount. Chặn render
 * cây route cho tới khi status rời khỏi 'checking' để RequireAuth không bao
 * giờ thấy trạng thái 'checking' (chỉ 'authenticated' hoặc 'anonymous').
 */
export default function AuthBootstrap({ children }: AuthBootstrapProps) {
  const status = useAuthStore((s) => s.status)

  useEffect(() => {
    if (status === 'checking') {
      void refreshSession()
    }
  }, [status])

  if (status === 'checking') {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Spin size="large" tip="Đang khôi phục phiên đăng nhập...">
          <div style={{ width: 240, height: 120 }} />
        </Spin>
      </div>
    )
  }

  return <>{children}</>
}
