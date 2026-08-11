import request from '@/utils/request.js'
import {
  isMockEnabled,
  mockLogin,
  mockGetUserInfo
} from '@/mock'

export function getUserInfo() {
  if (isMockEnabled()) {
    return mockGetUserInfo()
  }
  return request({
    url: '/user/info',
    method: 'get'
  })
}

export function login(data) {
  if (isMockEnabled()) {
    return mockLogin(data)
  }
  return request({
    url: '/login',
    method: 'post',
    data
  })
}
