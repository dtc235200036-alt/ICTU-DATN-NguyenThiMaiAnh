import { Navigate, Route, Routes } from 'react-router'

import { collectRoutes } from './app/registry'

export default function App() {
  const routes = collectRoutes()

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/tong-quan" replace />} />
      {routes.map((route) => (
        <Route key={route.path} path={route.path} element={route.element} />
      ))}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
