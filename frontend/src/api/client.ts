const TOKEN_KEY = 'knpc_token'
const ROLE_KEY = 'knpc_role'
const USERNAME_KEY = 'knpc_username'

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function getRole() {
  return sessionStorage.getItem(ROLE_KEY)
}

export function getUsername() {
  return sessionStorage.getItem(USERNAME_KEY)
}

export function setSession(token: string, role: string, username: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
  sessionStorage.setItem(ROLE_KEY, role)
  sessionStorage.setItem(USERNAME_KEY, username)
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(ROLE_KEY)
  sessionStorage.removeItem(USERNAME_KEY)
}

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> | undefined),
  }
  const resp = await fetch(path, { ...options, headers })
  if (resp.status === 401) {
    clearSession()
    window.location.reload()
    throw new ApiError(401, 'Session expired')
  }
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail || detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, detail)
  }
  const contentType = resp.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return resp.json() as Promise<T>
  }
  return resp.text() as unknown as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export { ApiError }
