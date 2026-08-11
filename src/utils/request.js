import axios from 'axios'
import { getToken, clearAuth } from '@/utils/auth.js'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 15000
})

request.interceptors.request.use(
  (config) => {
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
    const res = response.data
    // 统一业务约定：{ code, data, message }
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 0 || res.code === 200) {
        return res
      }
      return Promise.reject(new Error(res.message || '请求失败'))
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
