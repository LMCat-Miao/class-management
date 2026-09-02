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

  if (permissionStore.isRoutesAdded) {
    permissionStore.reset()
    resetRouter()
  }

  if (whiteList.includes(to.path)) return true
  return '/login'
})
