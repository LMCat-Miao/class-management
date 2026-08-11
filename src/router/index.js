import { createRouter, createWebHistory } from 'vue-router'
import { constantRoutes } from './routes'

const router = createRouter({
  history: createWebHistory(),
  routes: [...constantRoutes]
})

const whiteRouteNames = new Set(['Login', 'Root'])

export function resetRouter() {
  router.getRoutes().forEach((route) => {
    if (route.name && !whiteRouteNames.has(route.name)) {
      router.removeRoute(route.name)
    }
  })
}

export default router
