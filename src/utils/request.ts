import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { getToken, clearAuth } from '@/utils/auth'
import type { ApiResult } from '@/types/api'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 15000
})

/** 防止 401 / 账号停用处理重入 */
let handlingSessionEnd = false

function endSessionAndRedirectToLogin(): void {
  if (handlingSessionEnd) return
  handlingSessionEnd = true
  clearAuth()
  Promise.all([
    import('@/stores/user'),
    import('@/stores/permission'),
    import('@/router')
  ])
    .then(([{ useUserStore }, { usePermissionStore }, routerMod]) => {
      const router = routerMod.default
      useUserStore().reset()
      usePermissionStore().reset()
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    })
    .finally(() => {
      handlingSessionEnd = false
    })
}

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data as ApiResult | unknown
    if (res && typeof res === 'object' && 'code' in res) {
      const body = res as ApiResult
      if (body.code === 0 || body.code === 200) {
        return body
      }
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const data = error.response?.data
    const errorCode =
      data && typeof data === 'object' && 'error' in data
        ? String((data as { error?: string }).error || '')
        : ''

    if (status === 401) {
      // Token 无效 / 未登录
      endSessionAndRedirectToLogin()
    } else if (status === 403 && errorCode === 'ACCOUNT_DISABLED') {
      // 教师停用等账号不可用：清会话；普通 403 不清除 Token
      endSessionAndRedirectToLogin()
    }

    const message =
      (data && typeof data === 'object' && 'message' in data
        ? String((data as { message?: string }).message || '')
        : '') ||
      error.message ||
      '网络异常'
    return Promise.reject(new Error(message))
  }
)

export default request
