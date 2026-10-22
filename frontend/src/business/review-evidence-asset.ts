import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, saveBlob, type Schemas } from './api'
import { createAssetDownload } from './asset-download'
import type { ReviewEvidenceSelection } from './review-evidence'
import type { BusinessSession } from './session'

export type ReviewEvidenceAssetSelection = {
  selection: ReviewEvidenceSelection | null
  evidence: Schemas['Evidence'] | null
  loaded: boolean
  busy: boolean
  page: unknown
}
type Session = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}

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
    Number(year) >= 1 &&
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
function reference(value: unknown): value is Schemas['ObjectRef'] {
  return (
    record(value) &&
    exact(value, ['object_id', 'version_id', 'sha256']) &&
    identifier(value.object_id) &&
    text(value.version_id) &&
    hash(value.sha256)
  )
}
function timeRange(value: unknown) {
  return (
    value === null ||
    (record(value) &&
      exact(value, ['start_ms', 'end_ms']) &&
      integer(value.start_ms, 0) &&
      integer(value.end_ms) &&
      value.end_ms > value.start_ms)
  )
}
function bbox(value: unknown) {
  if (value === null) return true
  if (!record(value) || !exact(value, ['x', 'y', 'width', 'height'])) return false
  const { x, y, width, height } = value
  return (
    typeof x === 'number' &&
    typeof y === 'number' &&
    typeof width === 'number' &&
    typeof height === 'number' &&
    [x, y, width, height].every(Number.isFinite) &&
    x >= 0 &&
    y >= 0 &&
    width > 0 &&
    height > 0 &&
    x + width <= 1 &&
    y + height <= 1
  )
}
function invalid(): never {
  throw new FormError(
    '仅能读取当前所选原始证据精确绑定的有效原件；引用或版本不匹配时不回退其他对象。',
  )
}
function originalEvidence(value: unknown): Schemas['Evidence'] {
  if (
    !record(value) ||
    !exact(value, [
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
    ]) ||
    !identifier(value.evidence_id) ||
    !identifier(value.case_id) ||
    !identifier(value.task_id) ||
    !integer(value.run_version) ||
    !integer(value.result_version) ||
    value.kind !== 'original' ||
    !identifier(value.asset_id) ||
    !reference(value.object_ref) ||
    !timeRange(value.time_range) ||
    !bbox(value.bbox) ||
    !text(value.mapping_version) ||
    (value.model_name !== null && !text(value.model_name)) ||
    (value.model_version !== null && !text(value.model_version)) ||
    !text(value.authorization_version) ||
    !hash(value.sha256) ||
    !integer(value.version) ||
    !dateTime(value.created_at) ||
    // This is only this reader's eligible original-download subset, not a general Evidence invariant.
    value.sha256 !== value.object_ref.sha256
  )
    invalid()
  return value as Schemas['Evidence']
}
function originalAsset(value: unknown, evidence: Schemas['Evidence']): Schemas['Asset'] {
  if (
    !record(value) ||
    !exact(value, [
      'asset_id',
      'case_id',
      'content_id',
      'source_id',
      'kind',
      'object_ref',
      'mime',
      'size_bytes',
      'duration_ms',
      'width',
      'height',
      'state',
      'version',
      'created_at',
    ]) ||
    !identifier(value.asset_id) ||
    !identifier(value.case_id) ||
    !identifier(value.content_id) ||
    !identifier(value.source_id) ||
    value.kind !== 'original' ||
    !reference(value.object_ref) ||
    !text(value.mime) ||
    !integer(value.size_bytes) ||
    (value.duration_ms !== null && !integer(value.duration_ms, 0)) ||
    (value.width !== null && !integer(value.width)) ||
    (value.height !== null && !integer(value.height)) ||
    value.state !== 'VALID' ||
    !integer(value.version) ||
    !dateTime(value.created_at) ||
    value.case_id.toLowerCase() !== evidence.case_id.toLowerCase() ||
    value.asset_id.toLowerCase() !== evidence.asset_id.toLowerCase() ||
    value.object_ref.object_id.toLowerCase() !== evidence.object_ref!.object_id.toLowerCase() ||
    value.object_ref.version_id !== evidence.object_ref!.version_id ||
    value.object_ref.sha256 !== evidence.object_ref!.sha256
  )
    invalid()
  const asset = value as Schemas['Asset']
  return {
    ...asset,
    asset_id: asset.asset_id.toLowerCase(),
    case_id: asset.case_id.toLowerCase(),
    object_ref: { ...asset.object_ref, object_id: asset.object_ref.object_id.toLowerCase() },
  }
}

export function createReviewEvidenceAsset(
  session: Session,
  selection: () => ReviewEvidenceAssetSelection,
  save: typeof saveBlob = saveBlob,
) {
  const state = shallowReactive({
    asset: null as Schemas['Asset'] | null,
    busy: false,
    loaded: false,
    error: '',
  })
  let generation = 0
  let disposed = false
  let boundSignature = ''
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
      session.has('asset.read'),
      session.has('asset.download'),
      selection(),
    ])
  }
  function target() {
    if (disposed) invalid()
    const user = session.state.user
    if (!user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (
      !['review.read', 'evidence.read', 'asset.read'].every((permission) => session.has(permission))
    )
      throw new ApiError(403, 'PERMISSION_REQUIRED')
    const input = selection()
    const context = input.selection
    if (
      !identifier(user.user_id) ||
      !identifier(user.org_id) ||
      !Array.isArray(user.roles) ||
      !Array.isArray(user.permissions) ||
      !Array.isArray(user.case_ids) ||
      input.loaded !== true ||
      input.busy !== false ||
      !context ||
      !identifier(context.caseId) ||
      !identifier(context.taskId) ||
      !integer(context.runVersion) ||
      !integer(context.resultVersion) ||
      typeof context.sourceKey !== 'string' ||
      !context.sourceKey.trim() ||
      (context.evidenceIds !== null &&
        (!Array.isArray(context.evidenceIds) ||
          !context.evidenceIds.length ||
          context.evidenceIds.some((id) => !identifier(id)) ||
          new Set(context.evidenceIds.map((id) => id.toLowerCase())).size !==
            context.evidenceIds.length))
    )
      invalid()
    if (
      !user.case_ids.some(
        (id) => identifier(id) && id.toLowerCase() === context.caseId.toLowerCase(),
      )
    )
      throw new ApiError(403, 'CASE_SCOPE_REQUIRED')
    const evidence = originalEvidence(input.evidence)
    if (
      evidence.case_id.toLowerCase() !== context.caseId.toLowerCase() ||
      evidence.task_id.toLowerCase() !== context.taskId.toLowerCase() ||
      evidence.run_version !== context.runVersion ||
      evidence.result_version !== context.resultVersion ||
      (context.evidenceIds !== null &&
        !context.evidenceIds.some(
          (id) => id.toLowerCase() === evidence.evidence_id.toLowerCase(),
        )) ||
      !record(input.page) ||
      !exact(input.page, ['items', 'next_cursor']) ||
      !Array.isArray(input.page.items) ||
      (input.page.next_cursor !== null && !text(input.page.next_cursor)) ||
      !input.page.items.some((item) => JSON.stringify(item) === JSON.stringify(evidence))
    )
      invalid()
    return evidence
  }
  const download = createAssetDownload(
    session,
    () => {
      let evidence: Schemas['Evidence'] | null = null
      let asset: Schemas['Asset'] | null = null
      try {
        if (boundSignature && signature() === boundSignature) {
          evidence = target()
          asset = originalAsset(state.asset, evidence)
        }
      } catch {
        /* An invalid or superseded selection cannot supply a downloadable object. */
      }
      return {
        caseId: evidence?.case_id ?? '',
        assetId: evidence?.asset_id ?? '',
        asset,
        loaded: state.loaded && !!asset,
        busy: state.busy,
      }
    },
    save,
  )
  function clear() {
    generation++
    boundSignature = ''
    download.clear()
    Object.assign(state, { asset: null, busy: false, loaded: false, error: '' })
  }
  function canLoad() {
    try {
      target()
      return true
    } catch {
      return false
    }
  }
  async function load() {
    if (disposed || state.busy) return
    clear()
    let evidence: Schemas['Evidence']
    try {
      evidence = target()
    } catch (error) {
      state.error = errorMessage(error)
      return
    }
    const version = generation
    const identity = signature()
    const current = () => !disposed && version === generation && identity === signature()
    state.busy = true
    try {
      const reply = await session.call<unknown>(`/assets/${evidence.asset_id.toLowerCase()}`)
      if (!current()) return
      target()
      state.asset = originalAsset(reply.data, evidence)
      boundSignature = identity
      state.loaded = true
    } catch (error) {
      if (current()) state.error = errorMessage(error)
    } finally {
      if (current()) state.busy = false
    }
  }
  const stop = watch(signature, clear, { flush: 'sync' })
  function dispose() {
    disposed = true
    stop()
    clear()
  }
  return {
    state,
    downloadState: download.state,
    canLoad,
    canDownload: () => !disposed && !state.busy && download.canDownload(),
    load,
    download: async () => {
      if (!disposed) await download.download()
    },
    clear,
    dispose,
  }
}
