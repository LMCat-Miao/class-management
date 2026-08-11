const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export function isMockEnabled() {
  return USE_MOCK
}

export const mockUser = {
  id: 1,
  username: 'admin',
  nickname: '管理员',
  role: 'admin'
}

const mockCourses = [
  { id: 1, name: 'Vue3 从入门到实战', category: '前端', status: '正常', teacher: '张老师' },
  { id: 2, name: 'AI 大模型应用开发', category: '人工智能', status: '正常', teacher: '李老师' },
  { id: 3, name: '算法与数据结构', category: '算法', status: '正常', teacher: '王老师' },
  { id: 4, name: 'Python 数据分析', category: '人工智能', status: '停用', teacher: '赵老师' },
  { id: 5, name: '前端工程化实践', category: '前端', status: '正常', teacher: '陈老师' }
]

function delay(data, ms = 300) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), ms)
  })
}

export function mockLogin(data) {
  const username = data?.username?.trim()
  const password = data?.password?.trim()

  if (!username || !password) {
    return Promise.reject(new Error('请输入用户名和密码'))
  }

  // 演示账号；开启 mock 时任意账号密码也可登录
  return delay({
    data: {
      token: 'mock-token-' + Date.now(),
      userInfo: {
        ...mockUser,
        username
      }
    }
  })
}

export function mockGetUserInfo() {
  return delay({
    data: mockUser
  })
}

export function mockGetCourseList(params = {}) {
  let list = [...mockCourses]

  if (params.name) {
    list = list.filter((item) => item.name.includes(params.name))
  }
  if (params.category) {
    const map = {
      frontend: '前端',
      ai: '人工智能',
      algorithm: '算法'
    }
    const category = map[params.category] || params.category
    list = list.filter((item) => item.category === category)
  }
  if (params.status !== undefined && params.status !== '') {
    const statusText = String(params.status) === '1' ? '正常' : '停用'
    list = list.filter((item) => item.status === statusText)
  }

  const page = Number(params.page) || 1
  const pageSize = Number(params.pageSize) || 10
  const start = (page - 1) * pageSize
  const end = start + pageSize

  return delay({
    data: {
      list: list.slice(start, end),
      total: list.length
    }
  })
}
