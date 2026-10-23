import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'
import { sourceDetail } from './sources'

type SourceSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
type AssetSelection = {
  caseId: string
  assetId: string
  asset: Schemas['Asset'] | null
  loaded: boolean
  busy: boolean
}

export function createAssetSourceReader(session: SourceSession, selection: () => AssetSelection) {
  const state = shallowReactive({
    data: null as Schemas['Source'] | null,
    busy: false,
    loaded: false,
    error: '',
  })
  let generation = 0
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
      session.has('asset.read'),
      session.has('source.read'),
      selection(),
    ])
  }
  function clear() {
    generation++
    Object.assign(state, { data: null, busy: false, loaded: false, error: '' })
  }
  function target() {
    if (!session.state.user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!session.has('asset.read') || !session.has('source.read'))
      throw new ApiError(403, 'PERMISSION_REQUIRED')
    const selected = selection()
    const asset = selected.asset
    const caseId = uuid(selected.caseId).toLowerCase()
    if (
      !selected.loaded ||
      selected.busy ||
      !asset ||
      uuid(asset.asset_id).toLowerCase() !== uuid(selected.assetId).toLowerCase() ||
      uuid(asset.case_id).toLowerCase() !== caseId ||
      !session.state.user.case_ids.some((id) => id.toLowerCase() === caseId)
    )
      throw new FormError('请先读取当前可见案件内的资产详情，再查询其来源。')
    return { caseId, sourceId: uuid(asset.source_id).toLowerCase() }
  }
  function canLoad() {
    try {
      target()
      return !disposed && !state.busy
    } catch {
      return false
    }
  }
  async function load() {
    if (disposed || state.busy) return
    clear()
    const version = generation
    const context = identity()
    const current = () => !disposed && version === generation && context === identity()
    try {
      const selected = target()
      state.busy = true
      const { data } = await session.call<Schemas['Source']>(`/sources/${selected.sourceId}`)
      if (!current()) return
      target()
      state.data = sourceDetail(data, selected.caseId, selected.sourceId)
      state.loaded = true
    } catch (error) {
      if (current()) state.error = errorMessage(error)
    } finally {
      if (version === generation) state.busy = false
    }
  }
  const stop = watch(identity, clear, { flush: 'sync' })
  function dispose() {
    disposed = true
    stop()
    clear()
  }
  return { state, canLoad, load, clear, dispose }
}
