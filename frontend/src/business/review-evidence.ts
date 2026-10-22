import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, type Reply, type Schemas } from './api'
import type { BusinessSession } from './session'

type EvidenceSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
export type ReviewEvidenceSelection = {
  caseId: string
  taskId: string
  runVersion: number
  resultVersion: number
  sourceKey: string
  evidenceIds: readonly string[] | null
}
const evidenceKeys = [
  'evidence_id',
  'case_id',
  'task_id',
  'run_version',
  'result_version',
  'kind',
  'asset_id',
  'object_ref',
  'time_range',
  'bbox',
  'mapping_version',
  'model_name',
  'model_version',
  'authorization_version',
  'sha256',
  'version',
  'created_at',
]
const kinds = [
  'original',
  'frame',
  'region',
  'segment',
  'match',
  'text',
  'snapshot',
  'model_output',
]
function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
function exact(value: Record<string, unknown>, keys: string[]) {
  return Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key))
}
function identifier(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(value)
}
function text(value: unknown, maximum = 128): value is string {
  return typeof value === 'string' && [...value].length >= 1 && [...value].length <= maximum
}
function integer(value: unknown, minimum = 1): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum
}
function hash(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)
}
function dateTime(value: unknown): value is string {
  if (typeof value !== 'string') return false
  const parts =
    /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?([Zz]|[+-]\d{2}:\d{2})$/.exec(
      value,
    )
  if (!parts) return false
  const [, year, month, day, hour, minute, second, offset] = parts
  const calendar = new Date(`${year}-${month}-${day}T00:00:00Z`)
  const zone = offset!.toUpperCase()
  return (
    calendar.getUTCFullYear() === Number(year) &&
    calendar.getUTCMonth() + 1 === Number(month) &&
    calendar.getUTCDate() === Number(day) &&
    Number(hour) <= 23 &&
    Number(minute) <= 59 &&
    Number(second) <= 59 &&
    (zone === 'Z' || (Number(zone.slice(1, 3)) <= 23 && Number(zone.slice(4, 6)) <= 59)) &&
    Number.isFinite(Date.parse(value))
  )
}
function invalid(): never {
  throw new FormError('证据响应结构、案件任务绑定或历史版本无效，已拒绝显示。')
}
function objectRef(value: unknown) {
  if (value === null) return
  if (
    !record(value) ||
    !exact(value, ['object_id', 'version_id', 'sha256']) ||
    !identifier(value.object_id) ||
    !text(value.version_id) ||
    !hash(value.sha256)
  )
    invalid()
}
function timeRange(value: unknown) {
  if (value === null) return
  if (
    !record(value) ||
    !exact(value, ['start_ms', 'end_ms']) ||
    !integer(value.start_ms, 0) ||
    !integer(value.end_ms) ||
    value.end_ms <= value.start_ms
  )
    invalid()
}
function bbox(value: unknown) {
  if (value === null) return
  if (!record(value) || !exact(value, ['x', 'y', 'width', 'height'])) invalid()
  const { x, y, width, height } = value
  if (
    typeof x !== 'number' ||
    typeof y !== 'number' ||
    typeof width !== 'number' ||
    typeof height !== 'number' ||
    ![x, y, width, height].every(Number.isFinite) ||
    x < 0 ||
    y < 0 ||
    width <= 0 ||
    height <= 0 ||
    x > 1 ||
    y > 1 ||
    width > 1 ||
    height > 1 ||
    x + width > 1 ||
    y + height > 1
  )
    invalid()
}
function evidence(value: unknown, target: ReviewEvidenceSelection): Schemas['Evidence'] {
  if (
    !record(value) ||
    !exact(value, evidenceKeys) ||
    !identifier(value.evidence_id) ||
    !identifier(value.case_id) ||
    !identifier(value.task_id) ||
    value.case_id.toLowerCase() !== target.caseId ||
    value.task_id.toLowerCase() !== target.taskId ||
    !integer(value.run_version) ||
    value.run_version !== target.runVersion ||
    !integer(value.result_version) ||
    value.result_version !== target.resultVersion ||
    !identifier(value.asset_id) ||
    typeof value.kind !== 'string' ||
    !kinds.includes(value.kind) ||
    !text(value.mapping_version) ||
    !text(value.authorization_version) ||
    (value.model_name !== null && !text(value.model_name)) ||
    (value.model_version !== null && !text(value.model_version)) ||
    !hash(value.sha256) ||
    !integer(value.version) ||
    !dateTime(value.created_at)
  )
    invalid()
  objectRef(value.object_ref)
  timeRange(value.time_range)
  bbox(value.bbox)
  const item = value as Schemas['Evidence']
  return {
    ...item,
    object_ref: item.object_ref && { ...item.object_ref },
    time_range: item.time_range && { ...item.time_range },
    bbox: item.bbox && { ...item.bbox },
  }
}
function page(reply: Reply<unknown>, target: ReviewEvidenceSelection): Schemas['EvidencePage'] {
  const { data, history } = reply
  if (
    !history ||
    !identifier(history.taskId) ||
    history.taskId.toLowerCase() !== target.taskId ||
    history.runVersion !== String(target.runVersion) ||
    history.resultVersion !== String(target.resultVersion) ||
    !record(data) ||
    !exact(data, ['items', 'next_cursor']) ||
    !Array.isArray(data.items) ||
    (data.next_cursor !== null && !text(data.next_cursor))
  )
    invalid()
  const items = data.items.map((item) => evidence(item, target))
  if (new Set(items.map((item) => item.evidence_id.toLowerCase())).size !== items.length) invalid()
  return { items, next_cursor: data.next_cursor as string | null }
}

export function createReviewEvidenceReader(
  session: EvidenceSession,
  selection: () => ReviewEvidenceSelection | null,
) {
  const state = shallowReactive({
    data: null as Schemas['EvidencePage'] | null,
    busy: false,
    error: '',
    loaded: false,
    selectedId: '',
  })
  let generation = 0
  let disposed = false
  function signature() {
    const user = session.state.user
    return JSON.stringify([
      session.state.generation,
      user?.user_id,
      user?.org_id,
      user?.roles,
      user?.permissions,
      user?.case_ids,
      session.has('review.read'),
      session.has('evidence.read'),
      selection(),
    ])
  }
  function clear() {
    generation++
    Object.assign(state, { data: null, busy: false, error: '', loaded: false, selectedId: '' })
  }
  function target(): ReviewEvidenceSelection {
    const user = session.state.user
    if (!user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!session.has('review.read') || !session.has('evidence.read'))
      throw new ApiError(403, 'PERMISSION_REQUIRED')
    const value = selection()
    if (
      !value ||
      !identifier(value.caseId) ||
      !identifier(value.taskId) ||
      !integer(value.runVersion) ||
      !integer(value.resultVersion) ||
      typeof value.sourceKey !== 'string' ||
      !value.sourceKey.trim() ||
      (value.evidenceIds !== null &&
        (!Array.isArray(value.evidenceIds) ||
          !value.evidenceIds.length ||
          value.evidenceIds.some((id) => !identifier(id)) ||
          new Set(value.evidenceIds.map((id) => id.toLowerCase())).size !==
            value.evidenceIds.length))
    )
      throw new FormError('请选择有效的复核上下文或历史复核及其证据编号。')
    if (
      !user.case_ids.some(
        (id) => typeof id === 'string' && id.toLowerCase() === value.caseId.toLowerCase(),
      )
    )
      throw new ApiError(403, 'CASE_SCOPE_REQUIRED')
    return {
      ...value,
      caseId: value.caseId.toLowerCase(),
      taskId: value.taskId.toLowerCase(),
      evidenceIds: value.evidenceIds?.map((id) => id.toLowerCase()) ?? null,
    }
  }
  function canLoad() {
    if (disposed) return false
    try {
      target()
      return true
    } catch {
      return false
    }
  }
  async function load() {
    if (disposed) return
    clear()
    let value: ReviewEvidenceSelection
    try {
      value = target()
    } catch (error) {
      state.error = errorMessage(error)
      return
    }
    const version = generation
    const identity = signature()
    const current = () => !disposed && version === generation && identity === signature()
    state.busy = true
    try {
      const query = new URLSearchParams({
        'history[run_version]': String(value.runVersion),
        'history[result_version]': String(value.resultVersion),
      })
      const reply = await session.call<unknown>(`/analysis/tasks/${value.taskId}/evidence?${query}`)
      if (!current()) return
      target()
      state.data = page(reply, value)
      state.loaded = true
    } catch (error) {
      if (current()) state.error = errorMessage(error)
    } finally {
      if (current()) state.busy = false
    }
  }
  function visibleItems(): Schemas['Evidence'][] {
    if (!canLoad() || !state.data) return []
    const ids = target().evidenceIds
    return ids === null
      ? state.data.items
      : state.data.items.filter((item) => ids.includes(item.evidence_id.toLowerCase()))
  }
  function missingIds(): string[] {
    if (!canLoad() || !state.loaded) return []
    const ids = target().evidenceIds
    const found = new Set(state.data?.items.map((item) => item.evidence_id.toLowerCase()))
    return ids?.filter((id) => !found.has(id)) ?? []
  }
  function locate(id: string) {
    state.selectedId =
      identifier(id) &&
      visibleItems().some((item) => item.evidence_id.toLowerCase() === id.toLowerCase())
        ? id.toLowerCase()
        : ''
  }
  function selected(): Schemas['Evidence'] | null {
    return (
      visibleItems().find((item) => item.evidence_id.toLowerCase() === state.selectedId) ?? null
    )
  }
  const stop = watch(signature, clear, { flush: 'sync' })
  function dispose() {
    disposed = true
    stop()
    clear()
  }
  return { state, canLoad, load, locate, selected, visibleItems, missingIds, clear, dispose }
}
