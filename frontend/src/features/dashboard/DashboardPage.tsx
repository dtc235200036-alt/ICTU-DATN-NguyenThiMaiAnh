import { useAuthStore } from '../../stores/auth'
import BmDashboard from './BmDashboard'
import GvDashboard from './GvDashboard'
import SvDashboard from './SvDashboard'

const TITLE: Record<string, string> = {
  SINH_VIEN: 'Tổng quan',
  GIANG_VIEN: 'Tổng quan',
  BO_MON: 'Tổng quan toàn khoa',
}

// RequireAuth (App.tsx) đã đảm bảo user tồn tại trước khi route này render;
// mỗi vai trò render đúng widget MH-02/03/04 (Phase 2) của chính vai trò đó.
export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  if (!user) {
    return null
  }

  return (
    <div>
      <h2 style={{ margin: '0 0 20px' }}>{TITLE[user.vai_tro] ?? 'Tổng quan'}</h2>
      {user.vai_tro === 'SINH_VIEN' && <SvDashboard />}
      {user.vai_tro === 'GIANG_VIEN' && <GvDashboard />}
      {user.vai_tro === 'BO_MON' && <BmDashboard />}
    </div>
  )
}
