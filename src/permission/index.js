import router from '@/router'
import { getToken, removeToken } from '@/utils/auth.js'
import { useUserStore } from '@/stores/user.js'

const whiteList = ['/login']

router.beforeEach(async (to) => {
  const token = getToken()
  const userStore = useUserStore()

  if (token) {
    if (to.path === '/login') {
      return '/dashboard'
    }
    if (!userStore.userInfo) {
      try {
        await userStore.getUser()
      } catch {
        removeToken()
        userStore.clearUserInfo()
        return '/login'
      }
    }
    return true
  }

  if (whiteList.includes(to.path)) {
    return true
  }
  return '/login'
})
