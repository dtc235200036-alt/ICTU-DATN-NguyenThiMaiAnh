import { Card, Tag } from 'antd'

import { useAuthStore } from '../../stores/auth'

const ROLE_LABEL: Record<string, string> = {
  SINH_VIEN: 'Sinh viên',
  GIANG_VIEN: 'Giảng viên',
  BO_MON: 'Bộ môn',
}

// RequireAuth (App.tsx) đã đảm bảo user tồn tại trước khi route này render;
// không cần tự điều hướng /dang-nhap ở đây nữa (D-07).
export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  if (!user) {
    return null
  }

  return (
    <Card title="Tổng quan">
      <p>
        Xin chào, <strong>{user.ho_ten}</strong>
      </p>
      <Tag color="blue">{ROLE_LABEL[user.vai_tro] ?? user.vai_tro}</Tag>
    </Card>
  )
}
