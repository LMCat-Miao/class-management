import request from '@/utils/request.js'
import { isMockEnabled } from '@/mock'
import { mockLogin, mockGetUserInfo, mockLogout } from '@/mock/auth'

export function login(data) {
  if (isMockEnabled()) return mockLogin(data)
  return request({
    url: '/login',
    method: 'post',
    data
  })
}

export function getUserInfo() {
  if (isMockEnabled()) {
    const username = sessionStorage.getItem('mock_username') || 'admin'
    return mockGetUserInfo(username)
  }
  return request({
    url: '/user/info',
    method: 'get'
  })
}

export function logout() {
  if (isMockEnabled()) return mockLogout()
  return request({
    url: '/logout',
    method: 'post'
  })
}
