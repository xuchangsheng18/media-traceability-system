import { ApiError, resolveApiUrl } from '../api'
import type { components } from '../../../shared-contracts/generated/business-api'

export type Schemas = components['schemas']
export type Reply<T> = {
  data: T
  etag: string | null
  history?: {
    taskId: string | null
    runVersion: string | null
    resultVersion: string | null
  }
}
export class FormError extends Error {}

export class BusinessClient {
  private token = ''
  private generation = 0
  private pending = new Set<AbortController>()

  replaceToken(token: string) {
    if (
      /\s/.test(token) ||
      [...token].some(
        (character) => character.charCodeAt(0) <= 32 || character.charCodeAt(0) === 127,
      )
    )
      throw new Error('访问令牌格式不正确')
    this.generation++
    for (const controller of this.pending) controller.abort()
    this.pending.clear()
    this.token = token
  }

  async call<T>(
    path: string,
    body?: object,
    key?: string,
    etag?: string,
    binary = false,
  ): Promise<Reply<T>> {
    if (!this.token) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!path.startsWith('/') || path.startsWith('//') || path.includes('#'))
      throw new Error('请求地址无效')
    if (body && !key) throw new Error('变更请求缺少幂等键')
    const url = resolveApiUrl(
      path,
      import.meta.env.VITE_BUSINESS_API_BASE_URL ?? '/business/api/v1',
    )
    const version = this.generation
    const controller = new AbortController()
    this.pending.add(controller)
    const timeout = setTimeout(() => controller.abort(), 30_000)
    try {
      const headers: Record<string, string> = {
        Authorization: `Bearer ${this.token}`,
        Accept: binary ? 'application/octet-stream' : 'application/json',
      }
      if (body) headers['Content-Type'] = 'application/json'
      if (key) headers['Idempotency-Key'] = key
      if (etag) headers['If-Match'] = etag
      const response = await fetch(url, {
        method: body ? 'POST' : 'GET',
        headers,
        body: body ? JSON.stringify(body) : undefined,
        credentials: 'omit',
        redirect: 'error',
        cache: 'no-store',
        signal: controller.signal,
      })
      if (version !== this.generation) throw new Error('身份已切换，请重新查询')
      if (!response.ok) {
        const problem = await response.json().catch(() => ({}))
        if (version !== this.generation) throw new Error('身份已切换，请重新查询')
        const code =
          typeof problem.code === 'string' && /^[A-Z][A-Z0-9_]{0,95}$/.test(problem.code)
            ? problem.code
            : 'HTTP_ERROR'
        const requestId =
          typeof problem.request_id === 'string' && /^[a-f0-9-]{36}$/i.test(problem.request_id)
            ? problem.request_id
            : undefined
        throw new ApiError(response.status, code, requestId)
      }
      const data = binary ? await response.blob() : await response.json()
      if (version !== this.generation) throw new Error('身份已切换，请重新查询')
      return {
        data: data as T,
        etag: response.headers.get('ETag'),
        history: {
          taskId: response.headers.get('X-Task-Id'),
          runVersion: response.headers.get('X-Run-Version'),
          resultVersion: response.headers.get('X-Result-Version'),
        },
      }
    } finally {
      clearTimeout(timeout)
      this.pending.delete(controller)
    }
  }
}

export function uuid(value: string): string {
  if (!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(value))
    throw new FormError('请填写完整对象编号')
  return value
}

export function pageQuery(caseId: string, limit: number, cursor?: string | null): string {
  const values = new URLSearchParams({ case_id: uuid(caseId), limit: String(limit) })
  if (cursor) values.set('cursor', cursor)
  return values.toString()
}

export function errorMessage(error: unknown): string {
  if (error instanceof FormError) return error.message
  if (error instanceof ApiError) {
    const messages: Record<number, string> = {
      401: '身份未通过，请重新连接。',
      403: '当前身份没有此操作权限。',
      404: '对象不存在或不在当前访问范围。',
      409: '数据或审批已变化，请重新读取。',
      412: '版本已变化，请重新读取。',
      422: '填写内容或分页条件无效，请检查后重试。',
      428: '缺少当前对象版本，请先读取。',
      503: '身份、权限规则或依赖尚未就绪。',
    }
    return `${messages[error.status] ?? '请求失败，请稍后重试。'}（${error.code}）${error.requestId ? ` 请求编号：${error.requestId}` : ''}`
  }
  return '请求未完成，请检查连接；未确认结果的变更请使用原请求重试。'
}

export function saveBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
