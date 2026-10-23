import { shallowReactive, watch } from 'vue'
import { ApiError } from '../api'
import { errorMessage, FormError, uuid, type Schemas } from './api'
import type { BusinessSession } from './session'

type Part = Schemas['UploadPart']
type Upload = Schemas['UploadSession']
type Result = Schemas['UploadResult']
type Status = Schemas['UploadStatus']
type Intent =
  | { kind: 'create'; key: string; body: Schemas['UploadCreate'] }
  | { kind: 'part'; key: string; uploadId: string; body: Blob; part: Part }
  | { kind: 'complete'; key: string; uploadId: string; body: Schemas['UploadComplete'] }

const hashPattern = /^[a-f0-9]{64}$/
// Browser bookkeeping guard, not a server upload quota or business concurrency policy.
const maximumBrowserParts = 10_000
function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}
function exact(value: unknown, keys: string[]): value is Record<string, unknown> {
  return (
    record(value) &&
    Object.keys(value).length === keys.length &&
    keys.every((key) => Object.hasOwn(value, key))
  )
}
function positive(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0
}
function validId(value: unknown): value is string {
  if (typeof value !== 'string') return false
  try {
    uuid(value)
    return true
  } catch {
    return false
  }
}
async function sha256(blob: Blob): Promise<string> {
  const bytes = await blob.arrayBuffer()
  const hash = await crypto.subtle.digest('SHA-256', bytes)
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, '0')).join('')
}
function sessionResponse(value: unknown, expectedId?: string): Upload {
  if (
    !exact(value, ['upload_id', 'part_size_bytes', 'state', 'expires_at', 'version']) ||
    !validId(value.upload_id) ||
    (expectedId && value.upload_id !== expectedId) ||
    !positive(value.part_size_bytes) ||
    !positive(value.version) ||
    !['UPLOADING', 'VALIDATING', 'COMPLETED', 'REJECTED', 'EXPIRED'].includes(
      String(value.state),
    ) ||
    typeof value.expires_at !== 'string' ||
    !Number.isFinite(Date.parse(value.expires_at))
  )
    throw new FormError('上传会话响应无效，尚未确认请求结果。')
  return value as Upload
}
function resultResponse(value: unknown, id: string): Result {
  if (
    !exact(value, ['upload_id', 'asset_id', 'validation', 'duplicate_of', 'request_id']) ||
    value.upload_id !== id ||
    !validId(value.request_id) ||
    !['VALIDATING', 'VALID', 'REJECTED'].includes(String(value.validation)) ||
    (value.asset_id !== null && !validId(value.asset_id)) ||
    (value.duplicate_of !== null && !validId(value.duplicate_of)) ||
    (value.validation === 'VALID' ? !validId(value.asset_id) : value.asset_id !== null)
  )
    throw new FormError('上传结果响应无效，请查询当前实际状态。')
  return value as Result
}

export function createBusinessUploadController(
  session: BusinessSession,
  selection: () => { caseId: string; source: Schemas['Source'] | null },
  memoryBudgetBytes: number,
) {
  const state = shallowReactive({
    busy: false,
    error: '',
    message: '',
    uncertain: false,
    operation: '' as Intent['kind'] | '',
    filename: '',
    sizeBytes: 0,
    digest: '',
    session: null as Upload | null,
    status: null as Status | null,
    parts: [] as Part[],
    completionReceipt: null as Result | null,
    assetId: null as string | null,
  })
  let file: File | null = null
  let intent: Intent | null = null
  let serial = 0
  let disposed = false
  let expiryTimer: ReturnType<typeof setTimeout> | undefined
  const identity = () =>
    JSON.stringify([
      session.state.generation,
      session.state.user,
      selection().caseId,
      selection().source,
    ])
  function clear() {
    serial++
    file = null
    intent = null
    Object.assign(state, {
      busy: false,
      error: '',
      message: '',
      uncertain: false,
      operation: '',
      filename: '',
      sizeBytes: 0,
      digest: '',
      session: null,
      status: null,
      parts: [],
      completionReceipt: null,
      assetId: null,
    })
  }
  function scheduleExpiry() {
    clearTimeout(expiryTimer)
    const expiry = selection().source?.expires_at
    if (!expiry || disposed) return
    const remaining = Date.parse(expiry) - Date.now()
    if (!Number.isFinite(remaining) || remaining <= 0) return
    expiryTimer = setTimeout(
      () => {
        if (Date.parse(expiry) > Date.now()) {
          scheduleExpiry()
          return
        }
        clear()
        state.error = '来源上传授权已到期，已清除本页文件、会话与结果。'
      },
      Math.min(remaining, 2_147_483_647),
    )
  }
  const stop = watch(
    identity,
    () => {
      clear()
      scheduleExpiry()
    },
    { flush: 'sync' },
  )
  scheduleExpiry()
  function refuse(error: Error): never {
    clear()
    state.error = errorMessage(error)
    throw error
  }
  function authorize() {
    const user = session.state.user
    if (!user) throw new ApiError(401, 'AUTHENTICATION_REQUIRED')
    if (!session.has('asset.upload')) throw new ApiError(403, 'PERMISSION_REQUIRED')
    const selected = selection()
    const id = uuid(selected.caseId).toLowerCase()
    if (!user.case_ids.some((candidate) => candidate.toLowerCase() === id))
      throw new FormError('请先选择当前身份可见的案件。')
    const source = selected.source
    if (
      !source ||
      !validId(source.source_id) ||
      source.case_id.toLowerCase() !== id ||
      source.authorization_status !== 'verified' ||
      !source.purpose.includes('upload') ||
      !positive(source.version) ||
      (source.expires_at !== null &&
        (!Number.isFinite(Date.parse(source.expires_at)) ||
          Date.parse(source.expires_at) <= Date.now()))
    )
      refuse(new FormError('来源须属于当前案件，且具有有效的上传用途授权。'))
    return { caseId: id, source }
  }
  function boundFile(): File {
    if (!file || !state.digest) throw new FormError('请先选择并核验本地文件。')
    return file
  }
  function currentUpload(write = false): Upload {
    const current = state.session
    if (!current) throw new FormError('请先初始化业务上传。')
    if (
      write &&
      (current.state !== 'UPLOADING' ||
        state.completionReceipt ||
        Date.parse(current.expires_at) <= Date.now())
    )
      throw new FormError('会话已停止接收分片或已提交校验，请查询实际状态。')
    return current
  }
  function partCount(current: Upload): number {
    const count = Math.ceil(boundFile().size / current.part_size_bytes)
    if (!positive(count) || count > maximumBrowserParts)
      throw new FormError('分片数量超过本页资源预算，请使用已核验的其他接入方式。')
    return count
  }
  function partResponse(value: unknown, current: Upload): Part {
    if (
      !exact(value, ['part_no', 'size_bytes', 'sha256']) ||
      !positive(value.part_no) ||
      value.part_no > partCount(current) ||
      !positive(value.size_bytes) ||
      value.size_bytes !==
        Math.min(
          current.part_size_bytes,
          boundFile().size - (value.part_no - 1) * current.part_size_bytes,
        ) ||
      typeof value.sha256 !== 'string' ||
      !hashPattern.test(value.sha256)
    )
      throw new FormError('分片编号、大小或摘要响应无效。')
    return value as Part
  }
  function statusResponse(value: unknown, expected: Upload): Status {
    if (
      !exact(value, [
        'session',
        'result',
        'received_parts_count',
        'received_bytes',
        'total_size_bytes',
      ])
    )
      throw new FormError('上传进度响应不完整。')
    const current = sessionResponse(value.session, expected.upload_id)
    if (
      current.part_size_bytes !== expected.part_size_bytes ||
      current.version < expected.version ||
      value.total_size_bytes !== boundFile().size ||
      typeof value.received_parts_count !== 'number' ||
      !Number.isSafeInteger(value.received_parts_count) ||
      value.received_parts_count < 0 ||
      value.received_parts_count > partCount(current) ||
      typeof value.received_bytes !== 'number' ||
      !Number.isSafeInteger(value.received_bytes) ||
      value.received_bytes < 0 ||
      value.received_bytes > boundFile().size ||
      (value.received_parts_count === 0) !== (value.received_bytes === 0)
    )
      throw new FormError('上传进度与原始文件或会话不一致。')
    if (['UPLOADING', 'EXPIRED'].includes(current.state)) {
      if (value.result !== null) throw new FormError('上传状态与结果不一致。')
    } else {
      const result = resultResponse(value.result, current.upload_id)
      const expectedValidation = current.state === 'COMPLETED' ? 'VALID' : current.state
      if (
        result.validation !== expectedValidation ||
        (['VALIDATING', 'COMPLETED'].includes(current.state) &&
          (value.received_parts_count !== partCount(current) ||
            value.received_bytes !== boundFile().size))
      )
        throw new FormError('上传状态与结果不一致。')
    }
    return { ...value, session: current } as Status
  }
  function acceptStatus(value: Status) {
    state.session = value.session
    state.status = value
    state.assetId =
      value.session.state === 'COMPLETED' && value.result?.validation === 'VALID'
        ? value.result.asset_id
        : null
    state.message = state.assetId
      ? '服务端已完成校验；可在当前案件资产中继续读取。'
      : `服务端当前状态：${value.session.state}。`
  }
  async function perform(work: (isCurrent: () => boolean) => Promise<void>, retry = false) {
    if (disposed || state.busy) return
    state.error = ''
    if (intent && !retry) {
      state.error = '上次变更结果尚未确认，请重试原请求。'
      return
    }
    const version = serial
    const isCurrent = () => !disposed && version === serial
    state.busy = true
    try {
      authorize()
      await work(isCurrent)
    } catch (error) {
      if (isCurrent()) state.error = errorMessage(error)
    } finally {
      if (isCurrent()) state.busy = false
    }
  }
  async function transmit(request: Intent, isCurrent: () => boolean) {
    const wasUncertain = state.uncertain
    let sent = false
    intent = request
    state.operation = request.kind
    try {
      authorize()
      sent = true
      if (request.kind === 'create') {
        const { data } = await session.call<Upload>('/uploads', request.body, request.key)
        if (!isCurrent()) return
        authorize()
        const value = sessionResponse(data)
        if (value.state !== 'UPLOADING') throw new FormError('初始化回执状态无效，请重试原请求。')
        partCount(value)
        state.session = value
        state.message = '上传已初始化；会话编号仅为标识，每次请求仍核验权限。'
      } else if (request.kind === 'part') {
        const { data } = await session.putPart<Part>(
          `/uploads/${request.uploadId}/parts/${request.part.part_no}`,
          request.body,
          request.part.sha256,
          request.key,
        )
        if (!isCurrent()) return
        authorize()
        const value = partResponse(data, currentUpload())
        if (
          value.part_no !== request.part.part_no ||
          value.size_bytes !== request.part.size_bytes ||
          value.sha256 !== request.part.sha256
        )
          throw new FormError('分片回执与原字节不一致，请重试原请求。')
        state.parts = [...state.parts.filter((part) => part.part_no !== value.part_no), value].sort(
          (a, b) => a.part_no - b.part_no,
        )
        state.status = null
        state.message = `已确认 ${state.parts.length} 个分片；尚未完成资产校验。`
      } else {
        const { data } = await session.call<Result>(
          `/uploads/${request.uploadId}/complete`,
          request.body,
          request.key,
        )
        if (!isCurrent()) return
        authorize()
        state.completionReceipt = resultResponse(data, request.uploadId)
        state.status = null
        state.assetId = null
        state.message = '完成请求已受理；原回执不代表校验完成，请读取实际进度。'
      }
      intent = null
      state.uncertain = false
      state.operation = ''
    } catch (error) {
      if (isCurrent()) {
        state.uncertain =
          wasUncertain ||
          (sent && !(error instanceof ApiError && error.status >= 400 && error.status < 500))
        if (!state.uncertain) {
          intent = null
          state.operation = ''
        }
      }
      throw error
    }
  }
  async function choose(value: File | null) {
    await perform(async (isCurrent) => {
      if (state.session)
        throw new FormError('当前文件已绑定会话；请先明确结束本页流程再选择其他文件。')
      file = null
      Object.assign(state, { filename: '', sizeBytes: 0, digest: '' })
      if (!value) return
      if (
        !positive(memoryBudgetBytes) ||
        !positive(value.size) ||
        value.size > memoryBudgetBytes ||
        [...value.name].length < 1 ||
        [...value.name].length > 255 ||
        !['image/png', 'image/jpeg'].includes(value.type)
      )
        throw new FormError('当前仅支持非空PNG/JPEG文件，且大小不得超过本页摘要内存预算。')
      const digest = await sha256(value)
      if (!isCurrent()) return
      authorize()
      file = value
      Object.assign(state, {
        filename: value.name,
        sizeBytes: value.size,
        digest,
        message: '本地摘要已计算；尚未向服务端登记。',
      })
    })
  }
  async function create() {
    await perform(async (isCurrent) => {
      const selected = authorize()
      const original = boundFile()
      if (state.session) throw new FormError('已有上传会话，不重复创建。')
      await transmit(
        {
          kind: 'create',
          key: crypto.randomUUID(),
          body: {
            case_id: selected.caseId,
            source_id: selected.source.source_id,
            filename: original.name,
            size_bytes: original.size,
            mime: original.type,
            sha256: state.digest,
          },
        },
        isCurrent,
      )
    })
  }
  async function sendRemaining() {
    await perform(async (isCurrent) => {
      const current = currentUpload(true)
      const original = boundFile()
      for (let number = 1; number <= partCount(current); number++) {
        if (state.parts.some((part) => part.part_no === number)) continue
        authorize()
        const body = original.slice(
          (number - 1) * current.part_size_bytes,
          number * current.part_size_bytes,
        )
        const hash = await sha256(body)
        if (!isCurrent()) return
        await transmit(
          {
            kind: 'part',
            key: crypto.randomUUID(),
            uploadId: current.upload_id,
            body,
            part: { part_no: number, size_bytes: body.size, sha256: hash },
          },
          isCurrent,
        )
        if (!isCurrent()) return
      }
    })
  }
  async function complete() {
    await perform(async (isCurrent) => {
      const current = currentUpload(true)
      const count = partCount(current)
      if (
        state.parts.length !== count ||
        state.parts.some((part, index) => part.part_no !== index + 1)
      )
        throw new FormError('尚有未确认分片，不能提交完成请求。')
      await transmit(
        {
          kind: 'complete',
          key: crypto.randomUUID(),
          uploadId: current.upload_id,
          body: { parts: state.parts.map((part) => ({ ...part })) },
        },
        isCurrent,
      )
    })
  }
  async function readStatus(current: Upload) {
    const { data } = await session.call<Status>(`/uploads/${current.upload_id}`)
    return data
  }
  async function refresh() {
    await perform(async (isCurrent) => {
      const current = currentUpload()
      state.status = null
      state.assetId = null
      const data = await readStatus(current)
      if (!isCurrent()) return
      authorize()
      acceptStatus(statusResponse(data, current))
    })
  }
  async function reconcile() {
    await perform(async (isCurrent) => {
      const initial = currentUpload()
      const original = boundFile()
      state.parts = []
      state.status = null
      state.assetId = null
      const data = await readStatus(initial)
      if (!isCurrent()) return
      authorize()
      const first = statusResponse(data, initial)
      if (first.session.state !== 'UPLOADING') {
        acceptStatus(first)
        return
      }
      const collected: Part[] = []
      const cursors = new Set<string>()
      let cursor: string | null = null
      do {
        authorize()
        const query = new URLSearchParams({ limit: '100' })
        if (cursor) query.set('cursor', cursor)
        const { data: page } = await session.call<Schemas['UploadPartPage']>(
          `/uploads/${initial.upload_id}/parts?${query}`,
        )
        if (!isCurrent()) return
        authorize()
        if (
          !exact(page, ['items', 'next_cursor', 'session_version']) ||
          !Array.isArray(page.items) ||
          page.items.length > 100 ||
          page.session_version !== first.session.version ||
          (page.next_cursor !== null &&
            (typeof page.next_cursor !== 'string' ||
              !page.next_cursor ||
              page.next_cursor.length > 8192))
        )
          throw new FormError('分片分页版本或结构不一致，请从头核对。')
        for (const row of page.items) {
          const part = partResponse(row, first.session)
          if (part.part_no <= (collected.at(-1)?.part_no ?? 0))
            throw new FormError('分片编号重复或乱序，请从头核对。')
          const local = original.slice(
            (part.part_no - 1) * first.session.part_size_bytes,
            part.part_no * first.session.part_size_bytes,
          )
          const hash = await sha256(local)
          if (!isCurrent()) return
          if (hash !== part.sha256)
            throw new FormError('服务端分片与当前绑定文件不一致，已停止续传。')
          collected.push(part)
        }
        cursor = page.next_cursor as string | null
        if (cursor) {
          if (
            cursors.has(cursor) ||
            !page.items.length ||
            collected.length >= partCount(first.session)
          )
            throw new FormError('分片游标循环或超出文件边界，请从头核对。')
          cursors.add(cursor)
        }
      } while (cursor)
      const latest = await readStatus(first.session)
      if (!isCurrent()) return
      authorize()
      const final = statusResponse(latest, first.session)
      if (
        final.session.version !== first.session.version ||
        final.session.state !== 'UPLOADING' ||
        collected.length !== final.received_parts_count ||
        collected.reduce((total, part) => total + part.size_bytes, 0) !== final.received_bytes
      )
        throw new FormError('核对期间上传版本或进度发生变化，请从头核对。')
      state.parts = collected
      acceptStatus(final)
      state.message = '已逐片核对当前文件；可继续发送尚未接收的分片。'
    })
  }
  async function retry() {
    const request = intent
    if (!request || !state.uncertain) return
    await perform((isCurrent) => transmit(request, isCurrent), true)
  }
  function reset() {
    if (state.busy || state.uncertain) return
    clear()
  }
  function dispose() {
    disposed = true
    clearTimeout(expiryTimer)
    stop()
    clear()
  }
  return {
    state,
    choose,
    create,
    sendRemaining,
    complete,
    refresh,
    reconcile,
    retry,
    reset,
    dispose,
  }
}
