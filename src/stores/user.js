import { defineStore } from 'pinia'
import { getUserInfo } from '@/api/user.js'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null
  }),
  actions: {
    setUserInfo(info) {
      this.userInfo = info
    },
    async getUser() {
      const res = await getUserInfo()
      this.userInfo = res.data
    },
    clearUserInfo() {
      this.userInfo = null
    }
  }
})
