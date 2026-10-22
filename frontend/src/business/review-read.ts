import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, pageQuery, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type ReviewSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
type Target = { caseId: string; taskId: string }
const contextKeys = [
  'task_id',
  'run_version',
  'result_version',
  'policy_version',
  'snapshot_sha256',
  'object_version',
  'review_version',
]
const reviewKeys = [
  'review_id',
  'reviewer_id',
  'task_id',
  'run_version',
  'result_version',
  'expected_review_version',
  'decision',
  'reason',
  'evidence_ids',
  'policy_version',
  'review_version',
  'created_at',
]
const decisions = ['confirm_candidate', 'reject_candidate', 'return_for_evidence', 'request_rerun']

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
function exactKeys(value: Record<string, unknown>, keys: string[]) {
  return Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key))
}
function text(value: unknown, maximum: number): value is string {
  return typeof value === 'string' && [...value].length >= 1 && [...value].length <= maximum
}
function identifier(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(value)
}
function integer(value: unknown, minimum: number) {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum
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
  throw new FormError('复核响应结构、任务绑定或版本无效，已拒绝显示。')
}
function reviewContext(value: unknown, taskId: string): Schemas['ReviewContext'] {
  if (
    !record(value) ||
    !exactKeys(value, contextKeys) ||
    !identifier(value.task_id) ||
    value.task_id.toLowerCase() !== taskId ||
    !integer(value.run_version, 1) ||
    !integer(value.result_version, 1) ||
    !integer(value.object_version, 1) ||
    !integer(value.review_version, 0) ||
    !text(value.policy_version, 128) ||
    typeof value.snapshot_sha256 !== 'string' ||
    !/^[a-f0-9]{64}$/.test(value.snapshot_sha256)
  )
    invalid()
  return { ...(value as Schemas['ReviewContext']) }
}
function review(value: unknown, taskId: string): Schemas['Review'] {
  if (
    !record(value) ||
    !exactKeys(value, reviewKeys) ||
    !identifier(value.task_id) ||
    value.task_id.toLowerCase() !== taskId ||
    !identifier(value.review_id) ||
    !identifier(value.reviewer_id) ||
    !integer(value.run_version, 1) ||
    !integer(value.result_version, 1) ||
    !integer(value.expected_review_version, 0) ||
    !integer(value.review_version, 1) ||
    typeof value.decision !== 'string' ||
    !decisions.includes(value.decision) ||
    !text(value.reason, 4096) ||
    !text(value.policy_version, 128) ||
    !dateTime(value.created_at) ||
    !Array.isArray(value.evidence_ids) ||
    !value.evidence_ids.length ||
    value.evidence_ids.some((id) => !identifier(id)) ||
    new Set(value.evidence_ids.map((id: string) => id.toLowerCase())).size !==
      value.evidence_ids.length
  )
    invalid()
  const item = value as Schemas['Review']
  return { ...item, evidence_ids: [...item.evidence_ids] }
}
function reviewPage(value: unknown, taskId: string): Schemas['ReviewPage'] {
  if (
    !record(value) ||
    !exactKeys(value, ['items', 'next_cursor']) ||
    !Array.isArray(value.items) ||
    (value.next_cursor !== null && !text(value.next_cursor, 128))
  )
    invalid()
  return {
    items: value.items.map((item) => review(item, taskId)),
    next_cursor: value.next_cursor as string | null,
  }
}
function slot<T>() {
  return shallowReactive({ data: null as T | null, busy: false, error: '', loaded: false })
}

export function createTaskReviewReader(session: ReviewSession) {
  const context = slot<Schemas['ReviewContext']>()
  const history = slot<Schemas['ReviewPage']>()
  const state = { context, history }
  const generations = { context: 0, history: 0 }
  let selected = ''
  let disposed = false
  function identity() {
    const user = session.state.user
    return JSON.stringify([
      session.state.generation,
      user?.user_id,
      user?.org_id,
      user?.roles,
      user?.permissions,
      user?.case_ids,
      session.has('review.read'),
    ])
  }
  function clear() {
    selected = ''
    for (const name of ['context', 'history'] as const) {
      generations[name]++
      Object.assign(state[name], { data: null, busy: false, error: '', loaded: false })
    }
  }
  function target(caseId: string, taskId: string): Target {
    const user = session.state.user
    if (!user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!session.has('review.read')) throw new ApiError(403, 'PERMISSION_REQUIRED')
    const value = { caseId: uuid(caseId).toLowerCase(), taskId: uuid(taskId).toLowerCase() }
    if (!user.case_ids.some((id) => typeof id === 'string' && id.toLowerCase() === value.caseId))
      throw new ApiError(403, 'CASE_SCOPE_REQUIRED')
    return value
  }
  async function load<K extends keyof typeof state>(
    name: K,
    caseId: string,
    taskId: string,
    read: (value: Target) => Promise<(typeof state)[K]['data']>,
  ) {
    if (disposed) return
    let value: Target
    try {
      value = target(caseId, taskId)
    } catch (error) {
      clear()
      state[name].error = errorMessage(error)
      return
    }
    const key = JSON.stringify(value)
    if (selected !== key) {
      clear()
      selected = key
    }
    const version = ++generations[name]
    const signature = identity()
    const current = () =>
      !disposed && selected === key && version === generations[name] && signature === identity()
    Object.assign(state[name], { data: null, busy: true, error: '', loaded: false })
    try {
      const data = await read(value)
      if (!current()) return
      target(caseId, taskId)
      Object.assign(state[name], { data, loaded: true })
    } catch (error) {
      if (current()) state[name].error = errorMessage(error)
    } finally {
      if (current()) state[name].busy = false
    }
  }
  function loadContext(caseId: string, taskId: string) {
    return load('context', caseId, taskId, async (value) => {
      const { data } = await session.call<Schemas['ReviewContext']>(
        `/analysis/tasks/${value.taskId}/review-context`,
      )
      return reviewContext(data, value.taskId)
    })
  }
  function loadHistory(caseId: string, taskId: string, cursor?: string | null) {
    return load('history', caseId, taskId, async (value) => {
      if (cursor !== undefined && cursor !== null && !text(cursor, 128))
        throw new FormError('复核历史分页游标无效，请重新读取首页。')
      const query = new URLSearchParams(pageQuery(value.caseId, 20, cursor))
      query.set('task_id', value.taskId)
      const { data } = await session.call<Schemas['ReviewPage']>(`/reviews?${query}`)
      return reviewPage(data, value.taskId)
    })
  }
  const stop = watch(identity, clear, { flush: 'sync' })
  function dispose() {
    disposed = true
    stop()
    clear()
  }
  return { state, loadContext, loadHistory, clear, dispose }
}
