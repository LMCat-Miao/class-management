export function isMockEnabled() {
  return import.meta.env.VITE_USE_MOCK === 'true'
}

export function delay(data, ms = 300) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), ms)
  })
}

export function ok(data, message = 'ok') {
  return delay({ code: 0, data, message })
}

export function fail(message = '请求失败', code = 1) {
  return delay({ code, data: null, message }).then((res) => {
    return Promise.reject(new Error(res.message))
  })
}

export function paginate(list, params = {}) {
  const page = Number(params.page) || 1
  const pageSize = Number(params.pageSize) || 10
  const start = (page - 1) * pageSize
  return {
    list: list.slice(start, start + pageSize),
    total: list.length,
    page,
    pageSize
  }
}
