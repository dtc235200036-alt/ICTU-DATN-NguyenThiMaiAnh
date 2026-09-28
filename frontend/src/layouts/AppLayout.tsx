import { useMemo } from 'react'
import { Avatar, Breadcrumb, Button, Layout, Menu, Tag } from 'antd'
import { Outlet, matchPath, useLocation, useNavigate } from 'react-router'
import { useQueryClient } from '@tanstack/react-query'

import { collectRoutes } from '../app/registry'
import NotificationBell from '../features/notifications/NotificationBell'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const { Header, Sider, Content } = Layout

const ROLE_LABEL: Record<string, string> = {
  SINH_VIEN: 'Sinh viên',
  GIANG_VIEN: 'Giảng viên',
  BO_MON: 'Bộ môn',
}

function initialsOf(hoTen: string): string {
  const parts = hoTen.trim().split(/\s+/).filter(Boolean)
  const last = parts[parts.length - 1] ?? ''
  return last.slice(0, 1).toUpperCase() || '?'
}

/**
 * D-09/AUTH-02: khung admin dùng chung cho mọi route đã xác thực — Sider tối
 * với menu lọc theo vai trò (collectRoutes), Header có breadcrumb + chuông
 * thông báo (NOTF-01) + người dùng + Đăng xuất. Chỉ render khi đã có user (RequireAuth đảm bảo điều đó).
 */
export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)

  const routes = useMemo(() => collectRoutes(), [])

  const menuItems = useMemo(() => {
    if (!user) return []
    return routes
      .filter((route) => route.menu && route.menu.roles.includes(user.vai_tro))
      .sort((a, b) => (a.menu?.order ?? 0) - (b.menu?.order ?? 0))
      .map((route) => ({
        key: route.menu?.to ?? route.path,
        label: route.menu?.label ?? route.path,
      }))
  }, [routes, user])

  // T-03 (bug pre-existing từ Phase 2): so khớp CHÍNH XÁC theo chuỗi bỏ sót
  // mọi route có tham số động (`/de-tai/:id`, `/kiem-tra-trung-lap/:taiLieuId`,
  // 03-02) — không route nào trong số đó từng hiện Breadcrumb. Dùng matchPath
  // (end: true) để khớp đúng pattern, giữ nguyên hành vi cho route tĩnh.
  const matchedRoute = useMemo(
    () =>
      routes.find((route) => matchPath({ path: route.path, end: true }, location.pathname) !== null),
    [routes, location.pathname],
  )

  const selectedKeys = useMemo(() => {
    if (matchedRoute?.menu) {
      return [matchedRoute.menu.to ?? matchedRoute.path]
    }
    let best: string | null = null
    for (const item of menuItems) {
      if (location.pathname.startsWith(item.key) && (!best || item.key.length > best.length)) {
        best = item.key
      }
    }
    return best ? [best] : []
  }, [matchedRoute, menuItems, location.pathname])

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      // D-07/T-02-16: đăng xuất luôn xóa trạng thái client dù API lỗi.
    }
    clear()
    queryClient.clear()
    navigate('/dang-nhap', { replace: true })
  }

  if (!user) {
    return null
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={220}>
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            paddingLeft: 20,
            color: '#fff',
            fontWeight: 600,
            fontSize: 16,
            borderBottom: '1px solid rgba(255,255,255,0.12)',
          }}
        >
          QL Đồ án CNTT
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            height: 64,
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Breadcrumb items={(matchedRoute?.breadcrumb ?? []).map((label) => ({ title: label }))} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <NotificationBell />
            <Avatar style={{ backgroundColor: '#1677ff' }}>{initialsOf(user.ho_ten)}</Avatar>
            <span>{user.ho_ten}</span>
            <Tag color="blue">{ROLE_LABEL[user.vai_tro] ?? user.vai_tro}</Tag>
            <Button onClick={handleLogout}>Đăng xuất</Button>
          </div>
        </Header>
        <Content style={{ padding: 24, background: '#f5f5f5' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
