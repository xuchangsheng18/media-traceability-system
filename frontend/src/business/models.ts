import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type ReadSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
type Page<T> = { items: T[]; next_cursor: string | null }

function validateModel(item: Schemas['Model']) {
  if (
    [
      item.name,
      item.version,
      item.capability,
      item.dataset_version,
      item.model_card_ref,
      item.license_record_ref,
      item.backend,
      item.environment_ref,
      item.status,
    ].some((value) => typeof value !== 'string' || !value.length) ||
    !/^[a-f0-9]{64}$/.test(item.digest) ||
    !Number.isSafeInteger(item.row_version) ||
    item.row_version < 1
  )
    throw new FormError('模型登记元数据不完整，已拒绝显示。')
}

function validateEvaluation(item: Schemas['Evaluation']) {
  uuid(item.model_id)
  if (
    [item.dataset_id, item.dataset_version, item.protocol_id, item.split, item.created_at].some(
      (value) => typeof value !== 'string' || !value.length,
    ) ||
    !Number.isSafeInteger(item.sample_count) ||
    item.sample_count < 1 ||
    !Number.isSafeInteger(item.failure_count) ||
    item.failure_count < 0 ||
    item.failure_count > item.sample_count ||
    !item.metrics ||
    !item.artifact_ref ||
    typeof item.artifact_ref.version_id !== 'string' ||
    !item.artifact_ref.version_id.length ||
    !/^[a-f0-9]{64}$/.test(item.artifact_ref.sha256)
  )
    throw new FormError('评测元数据不完整，已拒绝显示。')
  uuid(item.artifact_ref.object_id)
  for (const key of [
    'macro_f1',
    'recall',
    'iou',
    'recall_at_k',
    'ece',
    'boundary_mae_ms',
  ] as const) {
    const value = item.metrics[key]
    if (
      value !== null &&
      (typeof value !== 'number' ||
        !Number.isFinite(value) ||
        value < 0 ||
        (key !== 'boundary_mae_ms' && value > 1))
    )
      throw new FormError('评测指标不完整或无效，已拒绝显示。')
  }
}

function validatePage<T>(value: Page<T>, identifier: string): void {
  if (
    !value ||
    !Array.isArray(value.items) ||
    value.items.some((item) => !item || typeof item !== 'object' || Array.isArray(item)) ||
    !(
      value.next_cursor === null ||
      (typeof value.next_cursor === 'string' &&
        value.next_cursor.length >= 1 &&
        value.next_cursor.length <= 128)
    )
  )
    throw new FormError('目录响应不完整，已拒绝显示，请重新查询。')
  for (const item of value.items) {
    const id = (item as Record<string, unknown>)[identifier]
    if (typeof id !== 'string') throw new FormError('目录对象编号无效，已拒绝显示。')
    uuid(id)
    if (identifier === 'model_id') validateModel(item as Schemas['Model'])
    else validateEvaluation(item as Schemas['Evaluation'])
  }
}

function organizationPage<T>(
  session: ReadSession,
  path: string,
  identifier: string,
  disposed: () => boolean,
) {
  const state = shallowReactive({
    data: null as Page<T> | null,
    loaded: false,
    busy: false,
    error: '',
    pageNumber: 0,
  })
  let generation = 0
  let pageSize = 20
  function clear() {
    generation++
    state.data = null
    state.loaded = false
    state.busy = false
    state.error = ''
    state.pageNumber = 0
  }
  async function request(limit: number, cursor: string | null, pageNumber: number) {
    if (disposed()) return
    clear()
    const version = generation
    const identity = session.state.generation
    const user = session.state.user?.user_id
    const org = session.state.user?.org_id
    function current() {
      return (
        !disposed() &&
        version === generation &&
        identity === session.state.generation &&
        user === session.state.user?.user_id &&
        org === session.state.user?.org_id
      )
    }
    state.busy = true
    try {
      if (!session.state.user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
      if (!session.has('model.read')) throw new ApiError(403, 'PERMISSION_REQUIRED')
      if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100)
        throw new FormError('每页条数须为1至100的整数。')
      // Organization is established by the authenticated server context only.
      const query = new URLSearchParams({ limit: String(limit) })
      if (cursor) query.set('cursor', cursor)
      const { data } = await session.call<Page<T>>(`${path}?${query.toString()}`)
      if (!current()) return
      if (!session.has('model.read')) throw new ApiError(403, 'PERMISSION_REQUIRED')
      validatePage(data, identifier)
      state.data = data
      state.loaded = true
      state.pageNumber = pageNumber
      pageSize = limit
    } catch (error) {
      if (current()) state.error = errorMessage(error)
    } finally {
      if (current()) state.busy = false
    }
  }
  async function load(limit = 20) {
    await request(limit, null, 1)
  }
  async function next() {
    const cursor = state.data?.next_cursor
    if (state.busy || !cursor) return
    await request(pageSize, cursor, state.pageNumber + 1)
  }
  return { state, clear, load, next }
}

export function createModelsReader(session: ReadSession) {
  let disposed = false
  const models = organizationPage<Schemas['Model']>(session, '/models', 'model_id', () => disposed)
  const evaluations = organizationPage<Schemas['Evaluation']>(
    session,
    '/model-evaluations',
    'evaluation_id',
    () => disposed,
  )
  function clear() {
    models.clear()
    evaluations.clear()
  }
  const stop = watch(
    () => [
      session.state.generation,
      session.state.user?.user_id,
      session.state.user?.org_id,
      session.has('model.read'),
    ],
    clear,
    { flush: 'sync' },
  )
  function dispose() {
    disposed = true
    stop()
    clear()
  }
  return { models, evaluations, clear, dispose }
}
