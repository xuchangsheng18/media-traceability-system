import { shallowReactive } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, saveBlob, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type DownloadSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation'>
}
type Selection = {
  caseId: string
  assetId: string
  asset: Schemas['Asset'] | null
  loaded: boolean
  busy: boolean
}

function selected(session: DownloadSession, selection: Selection) {
  if (!session.has('asset.download')) throw new ApiError(403, 'PERMISSION_REQUIRED')
  const asset = selection.asset
  if (
    !selection.loaded ||
    selection.busy ||
    !asset ||
    asset.state !== 'VALID' ||
    asset.case_id !== uuid(selection.caseId).toLowerCase() ||
    asset.asset_id !== uuid(selection.assetId).toLowerCase() ||
    !Number.isSafeInteger(asset.size_bytes) ||
    asset.size_bytes < 0 ||
    !asset.object_ref ||
    !/^[0-9a-f]{64}$/.test(asset.object_ref.sha256) ||
    !asset.object_ref.version_id
  )
    throw new FormError('请先读取当前案件内可下载资产的有效详情。')
  uuid(asset.object_ref.object_id)
  return asset
}

async function sha(data: ArrayBuffer) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('')
}

export function createAssetDownload(
  session: DownloadSession,
  selection: () => Selection,
  save: typeof saveBlob = saveBlob,
) {
  const state = shallowReactive({ busy: false, error: '', message: '' })
  let generation = 0
  function clear() {
    generation++
    state.busy = false
    state.error = ''
    state.message = ''
  }
  function canDownload() {
    try {
      selected(session, selection())
      return !state.busy
    } catch {
      return false
    }
  }
  async function download() {
    if (state.busy) return
    clear()
    const version = generation
    const identity = session.state.generation
    let snapshot = ''
    function current() {
      try {
        return (
          generation === version &&
          identity === session.state.generation &&
          JSON.stringify(selected(session, selection())) === snapshot
        )
      } catch {
        return false
      }
    }
    try {
      const asset = selected(session, selection())
      snapshot = JSON.stringify(asset)
      // Capture immutable values before waiting; detail replacement can invalidate every later stage.
      const id = asset.asset_id
      const size = asset.size_bytes
      const reference = { ...asset.object_ref }
      state.busy = true
      const reply = await session.call<Blob>(
        `/assets/${id}/content`,
        undefined,
        undefined,
        undefined,
        true,
      )
      if (!current()) return
      if (!(reply.data instanceof Blob) || reply.data.size !== size)
        throw new FormError('下载内容大小核验未通过，请重新读取资产详情。')
      const data = await reply.data.arrayBuffer()
      if (!current()) return
      // Python json.dumps uses ensure_ascii=True, including UTF-16 surrogate escapes.
      const identityJson = JSON.stringify([
        reference.object_id,
        reference.version_id,
        reference.sha256,
      ]).replace(
        /[\u007f-\uffff]/g,
        (character) => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'),
      )
      const [contentHash, objectHash] = await Promise.all([
        sha(data),
        sha(new TextEncoder().encode(identityJson).buffer),
      ])
      if (!current()) return
      if (contentHash !== reference.sha256 || reply.etag !== `"${objectHash}"`)
        throw new FormError('下载内容或固定版本核验未通过，请重新读取资产详情。')
      save(reply.data, `asset-${id}.bin`)
      state.message = '已核验大小、SHA-256和固定对象版本，并交由浏览器保存。'
    } catch (error) {
      if (generation === version && identity === session.state.generation)
        state.error = errorMessage(error)
    } finally {
      if (generation === version) state.busy = false
    }
  }
  return { state, clear, canDownload, download }
}
