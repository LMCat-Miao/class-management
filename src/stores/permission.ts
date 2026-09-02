import { defineStore } from 'pinia'
import type { RouteRecordRaw } from 'vue-router'
import router from '@/router'
import { asyncRoutes } from '@/router/routes'
import { ROLES } from '@/constants/roles'

export interface MenuItem {
  name: string
  path: string
}

function hasRouteRole(route: RouteRecordRaw, roles: string[]): boolean {
  const allow = route.meta?.roles as string[] | undefined
  if (!allow || !allow.length) return true
  return roles.some((role) => allow.includes(role))
}

function filterAsyncRoutes(
  routes: RouteRecordRaw[],
  roles: string[]
): RouteRecordRaw[] {
  const result: RouteRecordRaw[] = []
  routes.forEach((route) => {
    const item: RouteRecordRaw = { ...route }
    if (hasRouteRole(item, roles)) {
      if (item.children) {
        item.children = filterAsyncRoutes(item.children, roles)
      }
      result.push(item)
    }
  })
  return result
}

function buildMenus(routes: RouteRecordRaw[], roles: string[]): MenuItem[] {
  const menus: MenuItem[] = []
  routes.forEach((route) => {
    if (route.children?.length) {
      route.children.forEach((child) => {
        if (!child.meta?.menu) return
        const menuTitle = child.meta.menuTitle as
          | Record<string, string>
          | undefined
        const title =
          menuTitle?.[roles[0]] ||
          (child.meta.title as string) ||
          String(child.name)
        menus.push({
          name: title,
          path: child.path.startsWith('/') ? child.path : `/${child.path}`
        })
      })
    }
  })
  return menus
}

interface PermissionState {
  menus: MenuItem[]
  routes: RouteRecordRaw[]
  isRoutesAdded: boolean
}

export const usePermissionStore = defineStore('permission', {
  state: (): PermissionState => ({
    menus: [],
    routes: [],
    isRoutesAdded: false
  }),
  actions: {
    generateRoutes(roles: string[] = [ROLES.ADMIN]) {
      if (router.hasRoute('Root')) {
        router.removeRoute('Root')
      }

      const accessed = filterAsyncRoutes(asyncRoutes, roles)
      this.routes = accessed
      this.menus = buildMenus(accessed, roles)
      accessed.forEach((route) => router.addRoute(route))
      this.isRoutesAdded = true
      return accessed
    },
    reset() {
      this.menus = []
      this.routes = []
      this.isRoutesAdded = false
      if (!router.hasRoute('Root')) {
        router.addRoute({
          path: '/',
          name: 'Root',
          redirect: '/login'
        })
      }
    }
  }
})
