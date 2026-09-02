export interface ApiResult<T = unknown> {
  code: number
  data: T
  message: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

export interface LoginForm {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  nickname: string
  role: string
  roles: string[]
  permissions: string[]
  teacherId?: number
}

export interface LoginResult {
  accessToken: string
  refreshToken?: string
  token?: string
  userInfo: UserInfo
}
