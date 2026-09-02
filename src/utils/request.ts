import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { getToken, clearAuth } from '@/utils/auth'
import type { ApiResult } from '@/types/api'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 15000
})

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
    if (error.response?.status === 401) {
      clearAuth()
      import('@/router').then(({ default: router }) => {
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      })
    }
    const message =
      error.response?.data?.message || error.message || '网络异常'
    return Promise.reject(new Error(message))
  }
)

export default request
