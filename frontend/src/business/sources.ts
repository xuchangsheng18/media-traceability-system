import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, pageQuery, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type SourceSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
type Source = Schemas['Source']
type SourceCreate = Schemas['SourceCreate']
type SourcePage = { items: Source[]; next_cursor: string | null }
const createKeys = ['case_id', 'name', 'source_type', 'authorization_ref', 'purpose', 'expires_at']
const sourceTypes = ['authorized_business', 'public_licensed', 'user_submission', 'synthetic']
const statuses = ['pending', 'verified', 'expired', 'revoked']

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
function exactKeys(value: Record<string, unknown>, keys: string[]) {
  return Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key))
}
function text(value: unknown, maximum: number): value is string {
  return typeof value === 'string' && [...value].length >= 1 && [...value].length <= maximum
}

// Compare instants without passing fractional seconds through Date's millisecond precision.
// The server may reject a nonzero sub-microsecond expiry when its authority cannot represent it.
function expiryInstant(value: unknown): string | null {
  if (value === null) return null
  if (typeof value !== 'string') throw new FormError('有效期须为带时区的 RFC3339 时间或留空。')
  const parts =
    /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?([Zz]|[+-]\d{2}:\d{2})$/.exec(
      value,
    )
  if (!parts) throw new FormError('有效期须为带时区的 RFC3339 时间或留空。')
  const [, year, month, day, hour, minute, second, fraction = '', offset] = parts
  const calendar = new Date(`${year}-${month}-${day}T00:00:00Z`)
  const zone = offset!.toUpperCase()
  const instant = Date.parse(`${year}-${month}-${day}T${hour}:${minute}:${second}${zone}`)
  if (
    !Number.isFinite(instant) ||
    calendar.getUTCFullYear() !== Number(year) ||
    calendar.getUTCMonth() + 1 !== Number(month) ||
    calendar.getUTCDate() !== Number(day) ||
    Number(hour) > 23 ||
    Number(minute) > 59 ||
    Number(second) > 59 ||
    (zone !== 'Z' && (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4, 6)) > 59))
  )
    throw new FormError('有效期须为有效的带时区 RFC3339 时间。')
  return `${instant / 1000}|${fraction.replace(/0+$/, '')}`
}

function validateFields(value: Record<string, unknown>) {
  if (
    typeof value.case_id !== 'string' ||
    !text(value.name, 128) ||
    typeof value.source_type !== 'string' ||
    !sourceTypes.includes(value.source_type) ||
    !text(value.authorization_ref, 128) ||
    !Array.isArray(value.purpose) ||
    !value.purpose.length ||
    value.purpose.some((purpose) => !text(purpose, 128)) ||
    new Set(value.purpose).size !== value.purpose.length
  )
    throw new FormError('来源名称、类型、授权依据及不重复的用途须符合来源登记契约。')
  uuid(value.case_id)
  expiryInstant(value.expires_at)
}

function snapshot(value: SourceCreate, selectedCase: string): SourceCreate {
  if (!record(value) || !exactKeys(value, createKeys))
    throw new FormError('来源登记只能包含案件、名称、类型、授权依据、用途和有效期。')
  validateFields(value)
  if (value.case_id.toLowerCase() !== uuid(selectedCase).toLowerCase())
    throw new FormError('登记案件与当前选择不一致，请重新填写。')
  return {
    case_id: value.case_id,
    name: value.name,
    source_type: value.source_type,
    authorization_ref: value.authorization_ref,
    purpose: [...value.purpose],
    expires_at: value.expires_at,
  }
}

function validateSource(value: unknown, selectedCase: string): Source {
  if (
    !record(value) ||
    !exactKeys(value, [...createKeys, 'source_id', 'authorization_status', 'version'])
  )
    throw new FormError('来源响应结构不完整，已拒绝显示。')
  validateFields(value)
  if (
    typeof value.source_id !== 'string' ||
    typeof value.authorization_status !== 'string' ||
    !statuses.includes(value.authorization_status) ||
    !Number.isSafeInteger(value.version) ||
    Number(value.version) < 1 ||
    String(value.case_id).toLowerCase() !== selectedCase.toLowerCase()
  )
    throw new FormError('来源响应不属于当前案件或元数据无效，已拒绝显示。')
  uuid(value.source_id)
  return value as Source
}

function validateRegistration(value: unknown, body: SourceCreate): Source {
  const result = validateSource(value, body.case_id)
  if (
    result.name !== body.name ||
    result.source_type !== body.source_type ||
    result.authorization_ref !== body.authorization_ref ||
    JSON.stringify(result.purpose) !== JSON.stringify(body.purpose) ||
    expiryInstant(result.expires_at) !== expiryInstant(body.expires_at) ||
    !['pending', 'verified'].includes(result.authorization_status)
  )
    throw new FormError('登记响应与原请求不一致，结果尚未确认；请重试原登记请求。')
  return result
}

export function createSources(
  session: SourceSession,
  selection: () => string,
  draft: () => SourceCreate,
) {
  let disposed = false
  const identity = () =>
    JSON.stringify([
      session.state.generation,
      session.state.user?.user_id,
      session.state.user?.org_id,
      selection(),
    ])
  function authorize(permission: string) {
    if (!session.state.user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!session.has(permission)) throw new ApiError(403, 'PERMISSION_REQUIRED')
    uuid(selection())
  }
  const listState = shallowReactive({
    data: null as SourcePage | null,
    busy: false,
    error: '',
    loaded: false,
    pageNumber: 0,
  })
  const detailState = shallowReactive({
    data: null as Source | null,
    busy: false,
    error: '',
    loaded: false,
  })
  const registrationState = shallowReactive({
    data: null as Source | null,
    busy: false,
    error: '',
    message: '',
    uncertain: false,
  })
  let listVersion = 0
  let detailVersion = 0
  let registrationVersion = 0
  let pageSize = 20
  let intent: { body: SourceCreate; key: string; signature: string } | null = null

  function clearList() {
    listVersion++
    Object.assign(listState, { data: null, busy: false, error: '', loaded: false, pageNumber: 0 })
  }
  function clearDetail() {
    detailVersion++
    Object.assign(detailState, { data: null, busy: false, error: '', loaded: false })
  }
  function clearRegistration() {
    registrationVersion++
    intent = null
    Object.assign(registrationState, {
      data: null,
      busy: false,
      error: '',
      message: '',
      uncertain: false,
    })
  }
  function clear() {
    clearList()
    clearDetail()
    clearRegistration()
  }

  async function readPage(limit: number, cursor: string | null, pageNumber: number) {
    if (disposed) return
    clearList()
    const version = listVersion
    const actor = identity()
    const selectedCase = selection()
    const current = () => !disposed && version === listVersion && actor === identity()
    listState.busy = true
    try {
      authorize('source.read')
      if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100)
        throw new FormError('每页条数须为1至100的整数。')
      const { data } = await session.call<SourcePage>(
        `/sources?${pageQuery(selectedCase, limit, cursor)}`,
      )
      if (!current()) return
      authorize('source.read')
      if (
        !record(data) ||
        !exactKeys(data, ['items', 'next_cursor']) ||
        !Array.isArray(data.items) ||
        !(data.next_cursor === null || text(data.next_cursor, 128))
      )
        throw new FormError('来源分页响应不完整，已拒绝显示。')
      const items = data.items.map((item) => validateSource(item, selectedCase))
      if (new Set(items.map((item) => item.source_id.toLowerCase())).size !== items.length)
        throw new FormError('来源分页包含重复编号，已拒绝显示。')
      listState.data = { items, next_cursor: data.next_cursor }
      listState.loaded = true
      listState.pageNumber = pageNumber
      pageSize = limit
    } catch (error) {
      if (current()) listState.error = errorMessage(error)
    } finally {
      if (current()) listState.busy = false
    }
  }
  async function readDetail(sourceId: string) {
    if (disposed) return
    clearDetail()
    const version = detailVersion
    const actor = identity()
    const selectedCase = selection()
    const current = () => !disposed && version === detailVersion && actor === identity()
    detailState.busy = true
    try {
      authorize('source.read')
      const { data } = await session.call<Source>(`/sources/${uuid(sourceId)}`)
      if (!current()) return
      authorize('source.read')
      const item = validateSource(data, selectedCase)
      if (item.source_id.toLowerCase() !== sourceId.toLowerCase())
        throw new FormError('来源详情编号与请求不一致，已拒绝显示。')
      detailState.data = item
      detailState.loaded = true
    } catch (error) {
      if (current()) detailState.error = errorMessage(error)
    } finally {
      if (current()) detailState.busy = false
    }
  }

  async function send(retry: boolean) {
    if (disposed || registrationState.busy || registrationState.data) return
    let body: SourceCreate
    try {
      authorize('source.manage')
      body = snapshot(draft(), selection())
      if (intent && registrationState.uncertain) {
        if (!retry || JSON.stringify(body) !== intent.signature)
          throw new FormError('原登记结果尚未确认，请保留原输入并使用“重试原登记请求”。')
      } else {
        if (retry) return
        intent = { body, key: crypto.randomUUID(), signature: JSON.stringify(body) }
      }
    } catch (error) {
      registrationState.error = errorMessage(error)
      return
    }
    const request = intent!
    const previouslyUncertain = registrationState.uncertain
    const version = ++registrationVersion
    const actor = identity()
    const current = () => !disposed && version === registrationVersion && actor === identity()
    Object.assign(registrationState, { data: null, busy: true, error: '', message: '' })
    try {
      const { data } = await session.call<Source>('/sources', request.body, request.key)
      if (!current()) return
      authorize('source.manage')
      registrationState.data = validateRegistration(data, request.body)
      registrationState.uncertain = false
      intent = null
      registrationState.message =
        registrationState.data.authorization_status === 'pending'
          ? '登记成功，服务端状态：pending；尚不能作为有效用途授权。'
          : '登记成功，服务端状态：verified；后续操作仍须核验案件、用途及有效期。'
    } catch (error) {
      if (!current()) return
      registrationState.error = errorMessage(error)
      // A retry rejection cannot establish whether the original unknown request committed.
      registrationState.uncertain =
        previouslyUncertain ||
        !(error instanceof ApiError && error.status >= 400 && error.status < 500)
      if (!registrationState.uncertain) intent = null
    } finally {
      if (current()) registrationState.busy = false
    }
  }
  const stops = [
    watch(identity, clear, { flush: 'sync' }),
    watch(
      () => session.has('source.read'),
      () => {
        clearList()
        clearDetail()
      },
      { flush: 'sync' },
    ),
    watch(() => session.has('source.manage'), clearRegistration, { flush: 'sync' }),
    watch(
      () => JSON.stringify(draft()),
      () => {
        const unresolved = !!intent && (registrationState.busy || registrationState.uncertain)
        registrationVersion++
        Object.assign(registrationState, {
          data: null,
          busy: false,
          error: '',
          message: '',
          uncertain: unresolved,
        })
        if (!unresolved) intent = null
      },
      { flush: 'sync' },
    ),
  ]
  return {
    list: {
      state: listState,
      clear: clearList,
      load: (limit = 20) => readPage(limit, null, 1),
      next: async () => {
        if (listState.busy || !listState.data?.next_cursor) return
        await readPage(pageSize, listState.data.next_cursor, listState.pageNumber + 1)
      },
    },
    detail: { state: detailState, load: readDetail, clear: clearDetail },
    registration: { state: registrationState, submit: () => send(false), retry: () => send(true) },
    clear,
    dispose: () => {
      disposed = true
      stops.forEach((stop) => stop())
      clear()
    },
  }
}
