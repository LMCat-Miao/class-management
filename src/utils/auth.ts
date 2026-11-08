const ACCESS_TOKEN_KEY = 'access_token'
const LEGACY_TOKEN_KEY = 'token'
const LEGACY_REFRESH_KEY = 'refresh_token'

;['access_token', 'refresh_token', 'token', 'mock_username'].forEach((key) => {
  localStorage.removeItem(key)
})

function storage(): Storage {
  return sessionStorage
}

export function getToken(): string | null {
  return storage().getItem(ACCESS_TOKEN_KEY)
}

export function setToken(token: string): void {
  storage().setItem(ACCESS_TOKEN_KEY, token)
}

export function removeToken(): void {
  storage().removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(LEGACY_TOKEN_KEY)
}

/** 清理历史遗留的 refresh_token（本项目不再使用 refresh）。 */
function removeLegacyRefreshToken(): void {
  storage().removeItem(LEGACY_REFRESH_KEY)
  localStorage.removeItem(LEGACY_REFRESH_KEY)
}

export function clearAuth(): void {
  removeToken()
  removeLegacyRefreshToken()
  sessionStorage.removeItem('mock_username')
  localStorage.removeItem('mock_username')
}
