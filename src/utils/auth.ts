const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const LEGACY_TOKEN_KEY = 'token'

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

export function getRefreshToken(): string | null {
  return storage().getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string): void {
  storage().setItem(REFRESH_TOKEN_KEY, token)
}

export function removeRefreshToken(): void {
  storage().removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function clearAuth(): void {
  removeToken()
  removeRefreshToken()
  sessionStorage.removeItem('mock_username')
  localStorage.removeItem('mock_username')
}
