import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw
} from 'vue-router'
import { constantRoutes } from './routes'

const router = createRouter({
  history: createWebHistory(),
  routes: [...constantRoutes] as RouteRecordRaw[]
})

const whiteRouteNames = new Set(['Login', 'Root'])

export function resetRouter(): void {
  router.getRoutes().forEach((route) => {
    if (route.name && !whiteRouteNames.has(String(route.name))) {
      router.removeRoute(route.name)
    }
  })
}

export default router
