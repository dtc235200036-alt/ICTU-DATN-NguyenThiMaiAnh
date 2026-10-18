import { useState } from 'react'
import type { ReactNode } from 'react'
import { Alert, Button, Form, Input } from 'antd'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { api, getErrorMessage } from '../../api/client'
import logoIctu from '../../assets/logo-ictu.png'
import { useAuthStore } from '../../stores/auth'
import './LoginPage.css'

const FEATURES: { icon: ReactNode; title: string; text: string }[] = [
  {
    icon: <Icon d="M4 5h16v14H4z M8 9h8 M8 13h5" />,
    title: 'Giao đề tài & theo dõi tiến độ',
    text: 'GVHD giao đề tài, sinh viên báo cáo theo mốc, Bộ môn theo dõi toàn khoa.',
  },
  {
    icon: <Icon d="M6 3h9l3 3v15H6z M9 12l2 2 4-4" />,
    title: 'Duyệt đề cương hai cấp, ký số',
    text: 'GVHD duyệt và nộp lên Bộ môn; Lãnh đạo bộ môn phê duyệt bằng file đã ký số.',
  },
  {
    icon: <Icon d="M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14z M16 16l4 4" />,
    title: 'Kiểm tra trùng lặp bằng AI',
    text: 'So sánh ngữ nghĩa tên đề tài và nội dung đề cương, báo cáo với kho đồ án của khoa.',
  },
]

/** Biểu tượng nét mảnh dùng trong panel giới thiệu (không thêm thư viện icon). */
function Icon({ d }: { d: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  )
}

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
    <div className="login-page">
      <section className="login-brand" aria-label="Giới thiệu hệ thống">
        <div className="login-brand__head">
          <img className="login-logo" src={logoIctu} alt="Logo ICTU" />
          <div className="login-brand__school">
            Trường ĐH Công nghệ Thông tin
            <br />
            và Truyền thông — Khoa CNTT
          </div>
        </div>

        <div className="login-brand__body">
          <h1 className="login-brand__title">Hệ thống quản lý đồ án tốt nghiệp</h1>
          <p className="login-brand__desc">
            Một nơi cho sinh viên, giảng viên hướng dẫn và Bộ môn cùng theo dõi đồ án từ khi giao
            đề tài đến ngày bảo vệ.
          </p>
          <ul className="login-features">
            {FEATURES.map((f) => (
              <li key={f.title}>
                <span className="login-features__icon">{f.icon}</span>
                <div>
                  <div className="login-features__title">{f.title}</div>
                  <div className="login-features__text">{f.text}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="login-brand__foot">© {new Date().getFullYear()} Khoa Công nghệ thông tin — ICTU</div>
      </section>

      <main className="login-panel">
        <div className="login-form">
          <div className="login-form__mobile-head">
            <img className="login-logo" src={logoIctu} alt="Logo ICTU" />
            <strong>Hệ thống quản lý đồ án tốt nghiệp</strong>
          </div>

          <h2 className="login-form__title">Đăng nhập</h2>
          <p className="login-form__subtitle">Sử dụng tài khoản do Bộ môn cấp để tiếp tục.</p>

          {error && (
            <Alert
              style={{ marginBottom: 20 }}
              type="error"
              showIcon
              message="Sai thông tin đăng nhập hoặc tài khoản đã bị khóa"
              description="Kiểm tra lại mã SV/GV hoặc email và mật khẩu. Nếu tài khoản đã bị khóa, liên hệ Bộ môn để được mở lại."
            />
          )}

          <Form layout="vertical" size="large" onFinish={onFinish} disabled={loading} requiredMark={false}>
            <Form.Item
              label="Mã SV/GV hoặc email"
              name="dang_nhap"
              rules={[{ required: true, message: 'Vui lòng nhập mã SV/GV hoặc email' }]}
            >
              <Input autoComplete="username" placeholder="VD: DTC235200036 hoặc GV001" autoFocus />
            </Form.Item>
            <Form.Item
              label="Mật khẩu"
              name="mat_khau"
              rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}
            >
              <Input.Password autoComplete="current-password" placeholder="Nhập mật khẩu" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" block loading={loading}>
                Đăng nhập
              </Button>
            </Form.Item>
          </Form>

          <div className="login-hint">
            <b>Sinh viên</b> đăng nhập bằng mã sinh viên, <b>giảng viên</b> bằng mã GV hoặc email
            trường. Quên mật khẩu hoặc tài khoản bị khóa: liên hệ Bộ môn.
          </div>
        </div>
      </main>
    </div>
  )
}
