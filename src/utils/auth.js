const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const LEGACY_TOKEN_KEY = 'token'

// 清理历史 localStorage 登录态，避免打开站点直接进入首页
;['access_token', 'refresh_token', 'token', 'mock_username'].forEach((key) => {
  localStorage.removeItem(key)
})

function storage() {
  return sessionStorage
}

export function getToken() {
  return storage().getItem(ACCESS_TOKEN_KEY)
}

export function setToken(token) {
  storage().setItem(ACCESS_TOKEN_KEY, token)
}

export function removeToken() {
  storage().removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
}

export function getRefreshToken() {
  return storage().getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token) {
  storage().setItem(REFRESH_TOKEN_KEY, token)
}

export function removeRefreshToken() {
  storage().removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function clearAuth() {
  removeToken()
  removeRefreshToken()
  sessionStorage.removeItem('mock_username')
  localStorage.removeItem('mock_username')
}
