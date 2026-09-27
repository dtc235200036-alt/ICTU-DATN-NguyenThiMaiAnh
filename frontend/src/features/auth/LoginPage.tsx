import { useState } from 'react'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { api, getErrorMessage } from '../../api/client'
import { useAuthStore } from '../../stores/auth'

const { Title, Text } = Typography

interface LoginFormValues {
  dang_nhap: string
  mat_khau: string
}

interface FromLocationState {
  from?: {
    pathname: string
    search?: string
  }
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const status = useAuthStore((s) => s.status)
  const setSession = useAuthStore((s) => s.setSession)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // D-07: đã có phiên hợp lệ (vd. mở lại tab /dang-nhap) — không hiển thị lại form.
  if (status === 'authenticated') {
    return <Navigate to="/tong-quan" replace />
  }

  const onFinish = async (values: LoginFormValues) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post('/auth/login', values)
      setSession(data.access_token, data.nguoi_dung)
      const state = location.state as FromLocationState | null
      const from = state?.from
      const target = from ? `${from.pathname}${from.search ?? ''}` : '/tong-quan'
      navigate(target, { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f5f5',
      }}
    >
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ marginBottom: 0 }}>
            Hệ thống quản lý đồ án
          </Title>
          <Text type="secondary">Khoa Công nghệ thông tin</Text>
        </div>

        {error && (
          <Alert
            style={{ marginBottom: 16 }}
            type="error"
            showIcon
            message="Sai thông tin đăng nhập hoặc tài khoản đã bị khóa"
            description="Kiểm tra lại mã SV/GV hoặc email và mật khẩu. Nếu tài khoản đã bị khóa, liên hệ Bộ môn để được mở lại."
          />
        )}

        <Form layout="vertical" onFinish={onFinish} disabled={loading}>
          <Form.Item
            label="Mã SV/GV hoặc email"
            name="dang_nhap"
            rules={[{ required: true, message: 'Vui lòng nhập mã SV/GV hoặc email' }]}
          >
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="Mật khẩu"
            name="mat_khau"
            rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
          >
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Đăng nhập
            </Button>
          </Form.Item>
        </Form>

        <Text type="secondary" style={{ fontSize: 12 }}>
          Tài khoản do Bộ môn cấp. Liên hệ Bộ môn nếu quên mật khẩu.
        </Text>
      </Card>
    </div>
  )
}
