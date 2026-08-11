import { users } from './data'
import { ok, fail } from './index'

export function mockLogin(data) {
  const username = data?.username?.trim()
  const password = data?.password?.trim()

  if (!username || !password) {
    return fail('请输入用户名和密码')
  }

  const profile = users[username] || {
    ...users.admin,
    id: Date.now(),
    username,
    nickname: username,
    role: 'admin',
    roles: ['admin'],
    permissions: users.admin.permissions
  }

  // teacher 账号固定；其他账号按管理员演示
  const userInfo = username === 'teacher' ? { ...users.teacher } : { ...profile }

  return ok({
    accessToken: `mock-access-${username}-${Date.now()}`,
    refreshToken: `mock-refresh-${username}-${Date.now()}`,
    userInfo
  })
}

export function mockGetUserInfo(username) {
  if (username === 'teacher') {
    return ok({ ...users.teacher })
  }
  const user = users[username] || users.admin
  return ok({ ...user })
}

export function mockLogout() {
  return ok(true)
}
