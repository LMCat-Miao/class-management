import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import { mockLogin, mockGetUserInfo, mockLogout } from '@/mock/auth'
import type { ApiResult, LoginForm, LoginResult, UserInfo } from '@/types/api'

export function login(data: LoginForm): Promise<ApiResult<LoginResult>> {
  if (isMockEnabled()) return mockLogin(data)
  return request({
    url: '/login',
    method: 'post',
    data
  }) as Promise<ApiResult<LoginResult>>
}

export function getUserInfo(): Promise<ApiResult<UserInfo>> {
  if (isMockEnabled()) {
    const username = sessionStorage.getItem('mock_username') || 'admin'
    return mockGetUserInfo(username)
  }
  return request({
    url: '/user/info',
    method: 'get'
  }) as Promise<ApiResult<UserInfo>>
}

export function logout(): Promise<ApiResult<boolean>> {
  if (isMockEnabled()) return mockLogout()
  return request({
    url: '/logout',
    method: 'post'
  }) as Promise<ApiResult<boolean>>
}
