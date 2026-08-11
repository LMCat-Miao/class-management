import router, { resetRouter } from '@/router'
import { getToken, clearAuth } from '@/utils/auth'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'

const whiteList = ['/login']

router.beforeEach(async (to) => {
  const token = getToken()
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  if (token) {
    if (to.path === '/login') {
      return '/dashboard'
    }

    if (!permissionStore.isRoutesAdded) {
      try {
        if (!userStore.userInfo) {
          await userStore.getUser()
        }
        const roles = userStore.roles?.length
          ? userStore.roles
          : [userStore.userInfo?.role || 'admin']
        permissionStore.generateRoutes(roles)

        // 未登录占位根路径已被替换；访问 / 时进入首页
        if (to.path === '/') {
          return '/dashboard'
        }
        return { ...to, replace: true }
      } catch {
        await userStore.logout()
        permissionStore.reset()
        resetRouter()
        clearAuth()
        return '/login'
      }
    }

    if (to.path === '/') {
      return '/dashboard'
    }
    return true
  }

  // 未登录：清理动态路由痕迹，统一进登录页
  if (permissionStore.isRoutesAdded) {
    permissionStore.reset()
    resetRouter()
  }

  if (whiteList.includes(to.path)) return true
  return '/login'
})
