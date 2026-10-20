function hasControlOrSpace(value: string) {
  return [...value].some(
    (character) => character.charCodeAt(0) <= 32 || character.charCodeAt(0) === 127,
  )
}

function safePath(path: string) {
  let decoded: string
  try {
    decoded = decodeURIComponent(path)
  } catch {
    throw new Error('API_PATH_INVALID')
  }
  if (
    !decoded.startsWith('/') ||
    decoded.startsWith('//') ||
    decoded.includes('\\') ||
    hasControlOrSpace(decoded) ||
    /(^|\/)\.\.?($|\/)/.test(decoded)
  ) {
    throw new Error('API_PATH_INVALID')
  }
  return path
}

export function apiUrl(path: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  return resolveApiUrl(path, base)
}

export function resolveApiUrl(path: string, base: string): string {
  safePath(path)
  if (!base) return path
  try {
    if (base !== base.trim() || /[?#\\]/.test(base) || hasControlOrSpace(base)) throw new Error()
    if (base.startsWith('/')) return safePath(base.replace(/\/+$/, '') + path)
    const raw = /^https?:\/\/[^/?#]+(\/[^?#]*)?$/i.exec(base)
    if (!raw) throw new Error()
    safePath(raw[1] || '/')
    const url = new URL(base)
    if (
      !['http:', 'https:'].includes(url.protocol) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash
    )
      throw new Error()
    safePath(url.pathname)
    return url.href.replace(/\/+$/, '') + path
  } catch {
    throw new Error('API_BASE_INVALID')
  }
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly requestId?: string,
  ) {
    super(`请求失败：${status}（${code}）`)
  }
}

export async function request(path: string, token: string, body?: object, key?: string) {
  const url = apiUrl(path)
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (key) headers['Idempotency-Key'] = key
  const response = await fetch(url, {
    method: body ? 'POST' : 'GET',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    let payload: Record<string, unknown> = {}
    try {
      payload = await response.json()
    } catch {
      /* A non-JSON error is still a failed request. */
    }
    const code =
      typeof payload?.code === 'string' && /^[A-Z][A-Z0-9_]{0,95}$/.test(payload.code)
        ? payload.code
        : 'HTTP_ERROR'
    const id =
      typeof payload?.request_id === 'string' &&
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(payload.request_id)
        ? payload.request_id
        : undefined
    throw new ApiError(response.status, code, id)
  }
  return response.json()
}
