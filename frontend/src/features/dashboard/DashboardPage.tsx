import { useEffect } from 'react'
import { Card, Tag } from 'antd'
import { useNavigate } from 'react-router'

import { useAuthStore } from '../../stores/auth'

const ROLE_LABEL: Record<string, string> = {
  SINH_VIEN: 'Sinh viên',
  GIANG_VIEN: 'Giảng viên',
  BO_MON: 'Bộ môn',
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    if (!user) {
      navigate('/dang-nhap')
    }
  }, [user, navigate])

  if (!user) {
    return null
  }

  return (
    <div style={{ padding: 24 }}>
      <Card title="Tổng quan">
        <p>
          Xin chào, <strong>{user.ho_ten}</strong>
        </p>
        <Tag color="blue">{ROLE_LABEL[user.vai_tro] ?? user.vai_tro}</Tag>
      </Card>
    </div>
  )
}
