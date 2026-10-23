import { shallowReactive } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, pageQuery, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type ReadSession = Pick<BusinessSession, 'call' | 'has'>

function readSlot<T>() {
  const state = shallowReactive({ data: null as T | null, loaded: false, busy: false, error: '' })
  let generation = 0
  function clear() {
    generation++
    state.data = null
    state.loaded = false
    state.busy = false
    state.error = ''
  }
  async function read(load: () => Promise<T>) {
    clear()
    const version = generation
    state.busy = true
    try {
      const data = await load()
      if (version !== generation) return false
      state.data = data
      state.loaded = true
      return true
    } catch (error) {
      if (version === generation) state.error = errorMessage(error)
      return false
    } finally {
      if (version === generation) state.busy = false
    }
  }
  return { state, clear, read }
}

function requirePermission(session: ReadSession, permission: string) {
  if (!session.has(permission)) throw new ApiError(403, 'PERMISSION_REQUIRED')
}

function catalog<T extends { case_id: string }>(
  session: ReadSession,
  path: string,
  permission: string,
) {
  const page = readSlot<{ items: T[]; next_cursor: string | null }>()
  const state = shallowReactive({ ...page.state, caseId: '', pageNumber: 0 })
  const selection = { caseId: '', limit: 20, pageNumber: 0 }
  let generation = 0
  function clear() {
    generation++
    page.clear()
    Object.assign(state, page.state, { caseId: '', pageNumber: 0 })
    selection.caseId = ''
    selection.pageNumber = 0
  }
  async function request(caseId: string, limit: number, cursor: string | null, pageNumber: number) {
    const version = ++generation
    const pending = page.read(async () => {
      requirePermission(session, permission)
      const id = uuid(caseId).toLowerCase()
      if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100)
        throw new FormError('每页条数须为1至100的整数。')
      const { data } = await session.call<{ items: T[]; next_cursor: string | null }>(
        `${path}?${pageQuery(id, limit, cursor)}`,
      )
      if (data.items.some((item) => item.case_id !== id))
        throw new FormError('列表响应与查询案件不匹配，已拒绝显示。')
      return data
    })
    Object.assign(state, page.state, { caseId: '', pageNumber: 0 })
    const loaded = await pending
    if (version !== generation) return
    Object.assign(state, page.state)
    if (loaded) {
      selection.caseId = uuid(caseId).toLowerCase()
      selection.limit = limit
      selection.pageNumber = pageNumber
      state.caseId = selection.caseId
      state.pageNumber = pageNumber
    }
  }
  async function load(caseId: string, limit = 20) {
    clear()
    await request(caseId, limit, null, 1)
  }
  async function next() {
    const cursor = state.data?.next_cursor
    if (state.busy || !cursor || !selection.caseId) return
    await request(selection.caseId, selection.limit, cursor, selection.pageNumber + 1)
  }
  return { state, clear, load, next }
}

export const createAssetCatalog = (session: ReadSession) =>
  catalog<Schemas['Asset']>(session, '/assets', 'asset.read')
export const createTaskCatalog = (session: ReadSession) =>
  catalog<Schemas['Task']>(session, '/analysis/tasks', 'task.read')

export function createAssetReader(session: ReadSession) {
  const detail = readSlot<Schemas['Asset']>()
  async function load(caseId: string, assetId: string) {
    await detail.read(async () => {
      requirePermission(session, 'asset.read')
      const selectedCase = uuid(caseId).toLowerCase()
      const selectedAsset = uuid(assetId).toLowerCase()
      const { data } = await session.call<Schemas['Asset']>(`/assets/${selectedAsset}`)
      if (data.asset_id !== selectedAsset || data.case_id !== selectedCase)
        throw new FormError('资产详情与所选案件或对象不匹配，已拒绝显示。')
      return data
    })
  }
  return { state: detail.state, clear: detail.clear, load }
}
