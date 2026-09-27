import type { ReactNode } from 'react'

export type VaiTro = 'SINH_VIEN' | 'GIANG_VIEN' | 'BO_MON'

export interface MenuEntry {
  roles: VaiTro[]
  label: string
  order: number
  to?: string
}

export interface AppRoute {
  path: string
  element: ReactNode
  public?: boolean
  roles?: VaiTro[]
  breadcrumb?: string[]
  menu?: MenuEntry
}

interface RouteModule {
  routes: AppRoute[]
}

const modules = import.meta.glob<RouteModule>('../features/*/routes.tsx', {
  eager: true,
})

export function collectRoutes(): AppRoute[] {
  const routes: AppRoute[] = []
  for (const mod of Object.values(modules)) {
    routes.push(...mod.routes)
  }
  return routes
}
