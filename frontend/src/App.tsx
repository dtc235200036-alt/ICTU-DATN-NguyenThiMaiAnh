import { Route, Routes } from 'react-router'
import { Result } from 'antd'

import { collectRoutes } from './app/registry'
import AuthBootstrap from './features/auth/AuthBootstrap'
import RequireAuth from './features/auth/RequireAuth'
import AppLayout from './layouts/AppLayout'

export default function App() {
  const routes = collectRoutes()
  const publicRoutes = routes.filter((route) => route.public)
  const protectedRoutes = routes.filter((route) => !route.public)

  return (
    <AuthBootstrap>
      <Routes>
        {publicRoutes.map((route) => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}

        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          {protectedRoutes.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={<RequireAuth roles={route.roles}>{route.element}</RequireAuth>}
            />
          ))}
          <Route
            path="*"
            element={<Result status="404" title="404" subTitle="Không tìm thấy trang" />}
          />
        </Route>
      </Routes>
    </AuthBootstrap>
  )
}
