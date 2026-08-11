import { defineStore } from 'pinia'
import router from '@/router'
import { asyncRoutes } from '@/router/routes'
import { ROLES } from '@/constants/roles'

function hasRouteRole(route, roles) {
  const allow = route.meta?.roles
  if (!allow || !allow.length) return true
  return roles.some((role) => allow.includes(role))
}

function filterAsyncRoutes(routes, roles) {
  const result = []
  routes.forEach((route) => {
    const item = { ...route }
    if (hasRouteRole(item, roles)) {
      if (item.children) {
        item.children = filterAsyncRoutes(item.children, roles)
      }
      result.push(item)
    }
  })
  return result
}

function buildMenus(routes, roles) {
  const menus = []
  routes.forEach((route) => {
    if (route.children?.length) {
      route.children.forEach((child) => {
        if (!child.meta?.menu) return
        const title =
          child.meta.menuTitle?.[roles[0]] || child.meta.title || child.name
        menus.push({
          name: title,
          path: child.path.startsWith('/') ? child.path : `/${child.path}`
        })
      })
    }
  })
  return menus
}

export const usePermissionStore = defineStore('permission', {
  state: () => ({
    menus: [],
    routes: [],
    isRoutesAdded: false
  }),
  actions: {
    generateRoutes(roles = [ROLES.ADMIN]) {
      // 登录后移除「根路径 -> 登录页」的占位路由，再注册业务 Layout
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
      // 退出后恢复根路径到登录页
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
