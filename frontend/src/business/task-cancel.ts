import { shallowReactive } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type Session = Pick<BusinessSession, 'state' | 'has' | 'call'>
type Snapshot = { data: Readonly<Schemas['TaskExecutionStatus']>; etag: string; principal: string }
type Pending = {
  taskId: string
  body: Readonly<Schemas['TaskAction']>
  key: string
  etag: string
  principal: string
}
const requestable = new Set([
  'CREATED',
  'QUEUED',
  'RUNNING',
  'WAIT_REVIEW',
  'REVIEWING',
  'RETURNED',
])
const states = new Set([
  ...requestable,
  'SUCCEEDED',
  'FAILED',
  'CANCEL_REQUESTED',
  'CANCELLED',
  'ARCHIVED',
])

export function createTaskCancellation(session: Session) {
  const state = shallowReactive({
    execution: null as Readonly<Schemas['TaskExecutionStatus']> | null,
    receipt: null as Readonly<Schemas['Accepted']> | null,
    busy: false,
    accepted: false,
    pending: false,
    uncertain: false,
    error: '',
  })
  let generation = 0
  let snapshot: Snapshot | null = null
  let pending: Pending | null = null
  function principal() {
    const user = session.state.user
    return JSON.stringify([
      session.state.generation,
      user?.user_id,
      user?.org_id,
      [...(user?.permissions ?? [])].sort(),
      [...(user?.case_ids ?? [])].sort(),
      [...(user?.roles ?? [])].sort(),
    ])
  }
  function permitted() {
    return !!session.state.user && session.has('task.read') && session.has('task.cancel')
  }
  function reset() {
    generation++
    snapshot = null
    pending = null
    Object.assign(state, {
      execution: null,
      receipt: null,
      busy: false,
      accepted: false,
      pending: false,
      uncertain: false,
      error: '',
    })
  }
  function current(version: number, actor: string) {
    if (version !== generation) return false
    if (actor !== principal() || !permitted()) {
      reset()
      return false
    }
    return true
  }
  function canSubmit() {
    return (
      permitted() &&
      !!snapshot &&
      snapshot.principal === principal() &&
      !!session.state.user?.case_ids.includes(snapshot.data.case_id) &&
      requestable.has(snapshot.data.state) &&
      !state.busy &&
      !pending &&
      !state.accepted
    )
  }
  async function inspect(identifier: string) {
    if (state.busy || pending) return
    reset()
    const version = generation
    const actor = principal()
    try {
      if (!permitted()) throw new ApiError(403, 'PERMISSION_REQUIRED')
      const id = uuid(identifier).toLowerCase()
      state.busy = true
      const reply = await session.call<Schemas['TaskExecutionStatus']>(
        `/analysis/tasks/${id}/execution`,
      )
      if (!current(version, actor)) return
      const data = reply.data
      if (
        !data ||
        data.task_id !== id ||
        !session.state.user?.case_ids.includes(data.case_id) ||
        !states.has(data.state) ||
        !Number.isSafeInteger(data.run_version) ||
        data.run_version < 1 ||
        !Number.isSafeInteger(data.version) ||
        data.version < 1 ||
        !Number.isSafeInteger(data.result_version) ||
        data.result_version < 0 ||
        typeof data.result_available !== 'boolean' ||
        !reply.etag ||
        !/^"[\x21\x23-\x7e]{1,126}"$/.test(reply.etag)
      )
        throw new FormError('任务范围、版本或条件响应不完整，已拒绝取消。')
      const frozen = Object.freeze({ ...data })
      snapshot = { data: frozen, etag: reply.etag, principal: actor }
      state.execution = frozen
    } catch (error) {
      if (current(version, actor)) state.error = errorMessage(error)
    } finally {
      if (version === generation) state.busy = false
    }
  }
  async function submit(value: Pending) {
    const version = generation
    if (!current(version, value.principal)) return
    state.busy = true
    state.error = ''
    state.uncertain = false
    try {
      const reply = await session.call<Schemas['Accepted']>(
        `/analysis/tasks/${value.taskId}/cancel`,
        value.body,
        value.key,
        value.etag,
      )
      if (!current(version, value.principal)) return
      const data = reply.data
      if (
        !data ||
        data.task_id !== value.taskId ||
        data.state !== 'CANCEL_REQUESTED' ||
        data.status_url !== `/api/v1/analysis/tasks/${value.taskId}/execution`
      )
        throw new FormError('取消回执绑定不匹配，结果未确认；请重试原申请。')
      state.receipt = Object.freeze({ ...data })
      state.accepted = true
      state.pending = false
      pending = null
    } catch (error) {
      if (!current(version, value.principal)) return
      state.error = errorMessage(error)
      if (
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500 &&
        ![408, 429].includes(error.status)
      ) {
        snapshot = null
        pending = null
        state.execution = null
        state.pending = false
      } else state.uncertain = true
    } finally {
      if (version === generation) state.busy = false
    }
  }
  async function request(reason: string, approvalId: string, confirmed: boolean) {
    if (state.busy || pending) return
    state.error = ''
    try {
      if (!canSubmit() || !snapshot) throw new FormError('请先读取当前身份有权取消的任务条件。')
      if (!confirmed) throw new FormError('请先确认提交取消申请。')
      const text = reason.trim()
      if (!text || Array.from(text).length > 4096)
        throw new FormError('请填写1至4096字的取消原因。')
      const approval = approvalId.trim() ? uuid(approvalId.trim()).toLowerCase() : null
      const value: Pending = Object.freeze({
        taskId: snapshot.data.task_id,
        principal: snapshot.principal,
        etag: snapshot.etag,
        key: crypto.randomUUID(),
        body: Object.freeze({
          reason: text,
          approval_id: approval,
          expected_run_version: snapshot.data.run_version,
          expected_version: snapshot.data.version,
        }),
      })
      pending = value
      state.pending = true
      await submit(value)
    } catch (error) {
      state.error = errorMessage(error)
    }
  }
  async function retry() {
    if (!state.busy && state.uncertain && pending) await submit(pending)
  }
  return { state, inspect, request, retry, reset, canSubmit }
}
