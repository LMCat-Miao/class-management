export interface ApiResult<T = unknown> {
  code: number
  data: T
  message: string
  /** 稳定机器可读错误标识，如 ACCOUNT_DISABLED；成功响应通常无此字段 */
  error?: string
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
  /** @deprecated 后端已不再返回；保留可选字段仅兼容旧类型引用 */
  refreshToken?: string
  token?: string
  userInfo: UserInfo
}
