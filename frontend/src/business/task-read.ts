import { shallowReactive } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, pageQuery, uuid, type Reply, type Schemas } from './api'
import type { BusinessSession } from './session'

type ReadSession = Pick<BusinessSession, 'call' | 'has'>
export type ResultSelection = { taskId: string; runVersion: number; resultVersion: number }

function readSlot<T>() {
  const state = shallowReactive({ data: null as T | null, busy: false, loaded: false, error: '' })
  let generation = 0
  function clear() {
    generation++
    state.data = null
    state.busy = false
    state.loaded = false
    state.error = ''
  }
  async function read(load: () => Promise<T>): Promise<T | null> {
    clear()
    const version = generation
    state.busy = true
    try {
      const data = await load()
      if (version !== generation) return null
      state.data = data
      state.loaded = true
      return data
    } catch (error) {
      if (version === generation) state.error = errorMessage(error)
      return null
    } finally {
      if (version === generation) state.busy = false
    }
  }
  return { state, read, clear }
}

function requirePermission(session: ReadSession, permission: string) {
  if (!session.has(permission)) throw new ApiError(403, 'PERMISSION_REQUIRED')
}

function selection(value: ResultSelection): ResultSelection {
  if (
    !Number.isSafeInteger(value.runVersion) ||
    value.runVersion < 1 ||
    !Number.isSafeInteger(value.resultVersion) ||
    value.resultVersion < 1
  )
    throw new FormError('请填写大于零的运行版本和结果版本整数。')
  return {
    taskId: uuid(value.taskId).toLowerCase(),
    runVersion: value.runVersion,
    resultVersion: value.resultVersion,
  }
}

function historyQuery(value: ResultSelection, asset = false) {
  const query = new URLSearchParams()
  if (asset) query.set('history[task_id]', value.taskId)
  query.set('history[run_version]', String(value.runVersion))
  query.set('history[result_version]', String(value.resultVersion))
  return query.toString()
}

function historyData<T>(reply: Reply<T>, value: ResultSelection): T {
  const fail = () => {
    throw new FormError('历史响应版本绑定不完整或不匹配，已拒绝显示。')
  }
  if (
    reply.history?.taskId !== value.taskId ||
    reply.history?.runVersion !== String(value.runVersion) ||
    reply.history?.resultVersion !== String(value.resultVersion)
  )
    fail()
  const matches = (body: Record<string, unknown>) =>
    body.task_id === value.taskId &&
    body.run_version === value.runVersion &&
    body.result_version === value.resultVersion
  const body = reply.data as Record<string, unknown>
  if ('task_id' in body && !matches(body)) fail()
  if ('binding' in body && (!body.binding || !matches(body.binding as Record<string, unknown>)))
    fail()
  if (
    Array.isArray(body.items) &&
    body.items.some((item: Record<string, unknown>) => 'task_id' in item && !matches(item))
  )
    fail()
  return reply.data
}

export function createTaskReader(session: ReadSession) {
  const execution = readSlot<Schemas['TaskExecutionStatus']>()
  const nodes = readSlot<Schemas['NodePage']>()
  const events = readSlot<Schemas['TaskEventPage']>()
  const snapshot = readSlot<Schemas['Task']>()
  const risk = readSlot<Schemas['Findings']>()
  const forensics = readSlot<Schemas['Findings']>()
  const evidence = readSlot<Schemas['EvidencePage']>()
  const timeline = readSlot<Schemas['Timeline']>()
  let currentRun: { taskId: string; runVersion: number } | null = null
  let queryGeneration = 0
  let resultGeneration = 0
  function clearResults() {
    resultGeneration++
    for (const slot of [snapshot, risk, forensics, evidence, timeline]) slot.clear()
  }
  function reset() {
    queryGeneration++
    execution.clear()
    nodes.clear()
    events.clear()
    clearResults()
    currentRun = null
  }
  async function loadEvents(next = false) {
    const selected = currentRun
    const cursor = next ? events.state.data?.next_cursor : null
    if (!selected || (next && !cursor)) return
    await events.read(async () => {
      requirePermission(session, 'task.read')
      const query = new URLSearchParams({ run_version: String(selected.runVersion), limit: '20' })
      if (cursor) query.set('cursor', cursor)
      const { data } = await session.call<Schemas['TaskEventPage']>(
        `/analysis/tasks/${selected.taskId}/events?${query}`,
      )
      if (
        data.items.some(
          (event) => event.task_id !== selected.taskId || event.run_version !== selected.runVersion,
        )
      )
        throw new FormError('任务事件与所选任务或运行版本不匹配，已拒绝显示。')
      return data
    })
  }
  async function observe(identifier: string) {
    reset()
    const version = queryGeneration
    const current = await execution.read(async () => {
      requirePermission(session, 'task.read')
      const id = uuid(identifier).toLowerCase()
      const { data } = await session.call<Schemas['TaskExecutionStatus']>(
        `/analysis/tasks/${id}/execution`,
      )
      if (data.task_id !== id) throw new FormError('任务响应与查询对象不匹配，已拒绝显示。')
      return data
    })
    if (!current || version !== queryGeneration) return
    currentRun = { taskId: current.task_id, runVersion: current.run_version }
    await Promise.all([
      nodes.read(async () => {
        const { data } = await session.call<Schemas['NodePage']>(
          `/analysis/tasks/${current.task_id}/nodes?run_version=${current.run_version}`,
        )
        if (data.task_id !== current.task_id || data.run_version !== current.run_version)
          throw new FormError('节点响应与所选任务或运行版本不匹配，已拒绝显示。')
        return data
      }),
      loadEvents(),
    ])
  }
  async function loadResults(input: ResultSelection) {
    clearResults()
    const version = resultGeneration
    let selected: ResultSelection
    try {
      selected = selection(input)
    } catch (error) {
      await snapshot.read(() => Promise.reject(error))
      return
    }
    async function history<T>(suffix: string, permission: string) {
      requirePermission(session, permission)
      return historyData(
        await session.call<T>(
          `/analysis/tasks/${selected.taskId}${suffix}?${historyQuery(selected)}`,
        ),
        selected,
      )
    }
    const taskPromise = snapshot.read(() => history<Schemas['Task']>('', 'task.read'))
    const results = [
      risk.read(() => history<Schemas['Findings']>('/risk-findings', 'task.read')),
      forensics.read(() => history<Schemas['Findings']>('/forensics', 'task.read')),
      evidence.read(() => history<Schemas['EvidencePage']>('/evidence', 'evidence.read')),
    ]
    const task = await taskPromise
    if (task && version === resultGeneration)
      await timeline.read(async () => {
        requirePermission(session, 'asset.read')
        const data = historyData(
          await session.call<Schemas['Timeline']>(
            `/assets/${uuid(task.asset_id)}/timeline?${historyQuery(selected, true)}`,
          ),
          selected,
        )
        if (data.asset_id !== task.asset_id)
          throw new FormError('时间轴与历史媒体对象不匹配，已拒绝显示。')
        return data
      })
    await Promise.all(results)
  }
  return {
    execution,
    nodes,
    events,
    snapshot,
    risk,
    forensics,
    evidence,
    timeline,
    observe,
    loadEvents,
    loadResults,
    clearResults,
    reset,
  }
}

export function createPendingReviewReader(session: ReadSession) {
  const page = readSlot<Schemas['PendingReviewPage']>()
  async function load(caseId: string, cursor?: string | null) {
    await page.read(async () => {
      requirePermission(session, 'review.read')
      const id = uuid(caseId).toLowerCase()
      const { data } = await session.call<Schemas['PendingReviewPage']>(
        `/reviews/pending?${pageQuery(id, 20, cursor)}`,
      )
      if (data.items.some((item) => item.case_id !== id))
        throw new FormError('队列响应与查询案件不匹配，已拒绝显示。')
      return data
    })
  }
  return { state: page.state, clear: page.clear, load }
}

export function routeTaskId(value: unknown): string {
  if (typeof value !== 'string') return ''
  try {
    return uuid(value).toLowerCase()
  } catch {
    return ''
  }
}
