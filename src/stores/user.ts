import { defineStore } from 'pinia'
import { login as loginApi, getUserInfo, logout as logoutApi } from '@/api/user'
import {
  setToken,
  setRefreshToken,
  clearAuth,
  getToken
} from '@/utils/auth'
import type { LoginForm, UserInfo } from '@/types/api'

interface UserState {
  userInfo: UserInfo | null
  roles: string[]
  permissions: string[]
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userInfo: null,
    roles: [],
    permissions: []
  }),
  getters: {
    username: (state) => state.userInfo?.username || '',
    nickname: (state) =>
      state.userInfo?.nickname || state.userInfo?.username || '用户',
    hasPermission: (state) => (code?: string | string[]) => {
      if (!code) return true
      const codes = Array.isArray(code) ? code : [code]
      return codes.some((item) => state.permissions.includes(item))
    }
  },
  actions: {
    async login(form: LoginForm) {
      const res = await loginApi(form)
      const data = res.data
      setToken(data.accessToken || data.token || '')
      if (data.refreshToken) setRefreshToken(data.refreshToken)
      sessionStorage.setItem('mock_username', form.username)
      this.setProfile(data.userInfo)
      return data
    },
    setProfile(info: UserInfo | null | undefined) {
      this.userInfo = info || null
      this.roles = info?.roles || (info?.role ? [info.role] : [])
      this.permissions = info?.permissions || []
    },
    async getUser() {
      if (!getToken()) return null
      const res = await getUserInfo()
      this.setProfile(res.data)
      return res.data
    },
    async logout() {
      try {
        await logoutApi()
      } catch {
        // ignore
      }
      this.reset()
      clearAuth()
    },
    reset() {
      this.userInfo = null
      this.roles = []
      this.permissions = []
    },
    clearUserInfo() {
      this.reset()
    }
  }
})
