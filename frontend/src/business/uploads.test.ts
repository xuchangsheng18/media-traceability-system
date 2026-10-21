import { createHash } from 'node:crypto'
import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import type { Schemas } from './api'
import { createBusinessSession } from './session'

const caseId = '20000000-0000-4000-8000-000000000001'
const otherCase = '20000000-0000-4000-8000-000000000002'
const uploadId = '40000000-0000-4000-8000-000000000001'
const assetId = '50000000-0000-4000-8000-000000000001'
const digest = (text: string) => createHash('sha256').update(text).digest('hex')
const parts: Schemas['UploadPart'][] = [
  { part_no: 1, size_bytes: 2, sha256: digest('ab') },
  { part_no: 2, size_bytes: 1, sha256: digest('c') },
]
const upload: Schemas['UploadSession'] = {
  upload_id: uploadId,
  part_size_bytes: 2,
  state: 'UPLOADING',
  expires_at: '2099-01-01T00:00:00Z',
  version: 1,
}
const source: Schemas['Source'] = {
  case_id: caseId,
  source_id: '30000000-0000-4000-8000-000000000001',
  name: 'self-owned transport fixture, no business truth',
  source_type: 'synthetic',
  authorization_ref: 'self-owned-authority/1',
  purpose: ['upload'],
  expires_at: null,
  authorization_status: 'verified',
  version: 1,
}
function status(state: Schemas['UploadSession']['state'] = 'UPLOADING') {
  return {
    session: { ...upload, state, version: 3 },
    result:
      state === 'UPLOADING' || state === 'EXPIRED'
        ? null
        : {
            upload_id: uploadId,
            asset_id: state === 'COMPLETED' ? assetId : null,
            validation: state === 'COMPLETED' ? 'VALID' : state,
            duplicate_of: null,
            request_id: '60000000-0000-4000-8000-000000000001',
          },
    received_parts_count: 2,
    received_bytes: 3,
    total_size_bytes: 3,
  }
}
const active: { dispose(): void }[] = []
type Handler = (path: string, init: RequestInit) => Response | Promise<Response>
async function setup(permissions = ['source.read', 'asset.upload'], budget = 64) {
  const requests: { path: string; init: RequestInit }[] = []
  let handler: Handler = async (path, init) => {
    if (path === '/uploads') return Response.json(upload, { status: 201 })
    if (path === `/uploads/${uploadId}/complete`)
      return Response.json(status('VALIDATING').result, { status: 202 })
    if (init.method === 'PUT') return Response.json(parts[Number(path.split('/').at(-1)) - 1])
    if (path.includes('/parts?'))
      return Response.json({ items: parts, next_cursor: null, session_version: 3 })
    return Response.json(status())
  }
  vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
    if (url.endsWith('/auth/me'))
      return Response.json({
        user_id: '10000000-0000-4000-8000-000000000001',
        org_id: '10000000-0000-4000-8000-000000000002',
        roles: ['case_investigator'],
        permissions,
        case_ids: [caseId],
      })
    const path = url.replace('/business/api/v1', '')
    requests.push({ path, init })
    return handler(path, init)
  })
  const session = createBusinessSession()
  await session.connect('self-owned-upload-token')
  const selection = reactive({ caseId, source: { ...source } as Schemas['Source'] | null })
  const loader = import.meta.glob<{
    createBusinessUploadController: typeof import('./uploads').createBusinessUploadController
  }>('./uploads.ts')['./uploads.ts']
  expect(loader, 'the planned business upload controller is missing').toBeDefined()
  const controller = (await loader!()).createBusinessUploadController(
    session,
    () => selection,
    budget,
  )
  active.push(controller)
  const file = new File(['abc'], 'self-owned-bytes.png', { type: 'image/png' })
  return {
    session,
    selection,
    controller,
    file,
    requests,
    handle: (value: Handler) => (handler = value),
  }
}
afterEach(() => {
  active.splice(0).forEach((controller) => controller.dispose())
  vi.useRealTimers()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

test('source expiry actively clears a previously valid asset and retained file without a new request', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-10-22T00:00:00Z'))
  const ctx = await setup()
  ctx.selection.source!.expires_at = '2026-10-22T00:00:01Z'
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  ctx.handle(() => Response.json(status('COMPLETED')))
  await ctx.controller.refresh()
  expect(ctx.controller.state.assetId).toBe(assetId)
  const count = ctx.requests.length
  await vi.advanceTimersByTimeAsync(1001)
  expect(ctx.controller.state.assetId).toBeNull()
  expect(ctx.controller.state.status).toBeNull()
  expect(ctx.controller.state.session).toBeNull()
  expect(ctx.controller.state.digest).toBe('')
  expect(ctx.controller.state.error).not.toBe('')
  expect(ctx.requests).toHaveLength(count)
})

test('clock jump expiry refuses a new action and clears previous asset before reporting error', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-10-22T00:00:00Z'))
  const ctx = await setup()
  ctx.selection.source!.expires_at = '2026-10-22T00:00:01Z'
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  ctx.handle(() => Response.json(status('COMPLETED')))
  await ctx.controller.refresh()
  expect(ctx.controller.state.assetId).toBe(assetId)
  vi.setSystemTime(new Date('2026-10-22T00:00:02Z'))
  const count = ctx.requests.length
  await ctx.controller.refresh()
  expect(ctx.controller.state.assetId).toBeNull()
  expect(ctx.controller.state.status).toBeNull()
  expect(ctx.controller.state.digest).toBe('')
  expect(ctx.requests).toHaveLength(count)
})

test('late initialization after source expiry cannot restore file or session', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-10-22T00:00:00Z'))
  const ctx = await setup()
  ctx.selection.source!.expires_at = '2026-10-22T00:00:01Z'
  await ctx.controller.choose(ctx.file)
  let release!: (value: Response) => void
  ctx.handle(() => new Promise<Response>((resolve) => (release = resolve)))
  const request = ctx.controller.create()
  expect(ctx.requests).toHaveLength(1)
  await vi.advanceTimersByTimeAsync(1001)
  release(Response.json(upload))
  await request
  expect(ctx.controller.state.session).toBeNull()
  expect(ctx.controller.state.digest).toBe('')
})

test('late WebCrypto digest after identity change cannot restore the previous file', async () => {
  const ctx = await setup()
  let release!: (value: ArrayBuffer) => void
  const digestCall = vi
    .spyOn(crypto.subtle, 'digest')
    .mockImplementationOnce(() => new Promise<ArrayBuffer>((resolve) => (release = resolve)))
  const choosing = ctx.controller.choose(ctx.file)
  await vi.waitFor(() => expect(digestCall).toHaveBeenCalledTimes(1))
  ctx.session.disconnect()
  release(new Uint8Array(32).buffer)
  await choosing
  expect(ctx.controller.state.digest).toBe('')
  expect(ctx.controller.state.filename).toBe('')
  expect(ctx.requests).toHaveLength(0)
})

test('an uncertain original create rejected on retry still retains its original key and body', async () => {
  const ctx = await setup()
  ctx.handle(() => {
    throw new TypeError('self-owned lost original reply')
  })
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  const original = ctx.requests[0]!
  ctx.handle(() => Response.json({ code: 'PERMISSION_REQUIRED' }, { status: 403 }))
  await ctx.controller.retry()
  expect(ctx.controller.state.uncertain).toBe(true)
  ctx.handle(() => Response.json(upload))
  await ctx.controller.retry()
  expect(ctx.requests).toHaveLength(3)
  for (const request of ctx.requests) {
    expect(request.init.body).toBe(original.init.body)
    expect(request.init.headers).toEqual(original.init.headers)
  }
})

test.each(['valid', 'second-page-hash', 'final-count'])(
  'complete two-page receipt walk handles %s without trusting partial pages',
  async (fault) => {
    const ctx = await setup()
    await ctx.controller.choose(ctx.file)
    await ctx.controller.create()
    let statusReads = 0
    ctx.handle((path) => {
      if (!path.includes('/parts?')) {
        statusReads++
        const value = status()
        if (fault === 'final-count' && statusReads > 1) {
          value.received_parts_count = 1
          value.received_bytes = 2
        }
        return Response.json(value)
      }
      if (!path.includes('cursor='))
        return Response.json({ items: [parts[0]], next_cursor: 'a+b/c=', session_version: 3 })
      expect(path).toContain('cursor=a%2Bb%2Fc%3D')
      return Response.json({
        items: [
          { ...parts[1], sha256: fault === 'second-page-hash' ? 'a'.repeat(64) : parts[1]!.sha256 },
        ],
        next_cursor: null,
        session_version: 3,
      })
    })
    await ctx.controller.reconcile()
    expect(ctx.controller.state.parts).toEqual(fault === 'valid' ? parts : [])
    expect(ctx.controller.state.error === '').toBe(fault === 'valid')
    expect(ctx.requests.filter((request) => request.init.method === 'PUT')).toHaveLength(0)
  },
)

test('create uses only six exact fields and preserves file bytes hash', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  expect(ctx.requests).toHaveLength(1)
  expect(JSON.parse(String(ctx.requests[0]!.init.body))).toEqual({
    case_id: caseId,
    source_id: source.source_id,
    filename: 'self-owned-bytes.png',
    mime: 'image/png',
    size_bytes: 3,
    sha256: 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
  })
  expect(ctx.controller.state.session).toEqual(upload)
})

test.each(['missing-user', 'permission', 'membership', 'case', 'revoked', 'purpose', 'expired'])(
  '%s refuses upload before network',
  async (fault) => {
    const ctx = await setup()
    if (fault === 'missing-user') ctx.session.disconnect()
    if (fault === 'permission') ctx.session.state.user!.permissions = ['source.read']
    if (fault === 'membership') ctx.session.state.user!.case_ids = []
    if (fault === 'case') ctx.selection.source!.case_id = otherCase
    if (fault === 'revoked') ctx.selection.source!.authorization_status = 'revoked'
    if (fault === 'purpose') ctx.selection.source!.purpose = ['download']
    if (fault === 'expired') ctx.selection.source!.expires_at = '2000-01-01T00:00:00Z'
    await ctx.controller.choose(ctx.file)
    await ctx.controller.create()
    expect(ctx.requests).toHaveLength(0)
    expect(ctx.controller.state.error).not.toBe('')
    expect(ctx.controller.state.session).toBeNull()
  },
)

test.each([0, -1, NaN, Infinity, 1.5])(
  'invalid finite byte budget %s refuses hashing',
  async (budget) => {
    const ctx = await setup(['source.read', 'asset.upload'], budget)
    await ctx.controller.choose(ctx.file)
    await ctx.controller.create()
    expect(ctx.requests).toHaveLength(0)
    expect(ctx.controller.state.error).not.toBe('')
  },
)

test('file larger than browser resource budget is not read or transmitted', async () => {
  const ctx = await setup(['source.read', 'asset.upload'], 2)
  const read = vi.spyOn(ctx.file, 'arrayBuffer')
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  expect(read).not.toHaveBeenCalled()
  expect(ctx.requests).toHaveLength(0)
})

test('unknown create result retries identical original body and key without a new upload', async () => {
  const ctx = await setup()
  ctx.handle(() => {
    throw new TypeError('self-owned network interruption')
  })
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  expect(ctx.controller.state.uncertain).toBe(true)
  await ctx.controller.create()
  expect(ctx.requests).toHaveLength(1)
  ctx.handle(() => Response.json(upload, { status: 201 }))
  await ctx.controller.retry()
  expect(ctx.requests).toHaveLength(2)
  expect(ctx.requests[1]!.init.body).toBe(ctx.requests[0]!.init.body)
  expect(ctx.requests[1]!.init.headers).toEqual(ctx.requests[0]!.init.headers)
  expect(ctx.controller.state.uncertain).toBe(false)
  expect(ctx.controller.state.session?.upload_id).toBe(uploadId)
})

test('response with invalid session identity retains original request as uncertain', async () => {
  const ctx = await setup()
  ctx.handle(() => Response.json({ ...upload, upload_id: 'not-a-uuid' }))
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  expect(ctx.controller.state.uncertain).toBe(true)
  expect(ctx.controller.state.session).toBeNull()
})

test('parts follow server size and hash exact bytes, and cannot complete with missing receipts', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  await ctx.controller.complete()
  expect(ctx.requests).toHaveLength(1)
  await ctx.controller.sendRemaining()
  const sent = ctx.requests.filter((request) => request.init.method === 'PUT')
  expect(sent.map((request) => request.path)).toEqual([
    `/uploads/${uploadId}/parts/1`,
    `/uploads/${uploadId}/parts/2`,
  ])
  expect(await (sent[0]!.init.body as Blob).text()).toBe('ab')
  expect(await (sent[1]!.init.body as Blob).text()).toBe('c')
  expect(new Headers(sent[0]!.init.headers).get('X-Part-SHA256')).toBe(parts[0]!.sha256)
  expect(new Headers(sent[1]!.init.headers).get('Content-Length')).toBeNull()
  expect(ctx.controller.state.parts).toEqual(parts)
})

test('unknown part retry uses original bytes and key; other actions do not lose intent', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  ctx.handle(() => {
    throw new TypeError('self-owned lost part reply')
  })
  await ctx.controller.sendRemaining()
  expect(ctx.controller.state.uncertain).toBe(true)
  await ctx.controller.complete()
  await ctx.controller.choose(new File(['xyz'], 'other.png', { type: 'image/png' }))
  expect(ctx.requests).toHaveLength(2)
  ctx.handle(() => Response.json(parts[0]))
  await ctx.controller.retry()
  expect(ctx.requests).toHaveLength(3)
  expect(ctx.requests[1]!.init.headers).toEqual(ctx.requests[2]!.init.headers)
  expect(await (ctx.requests[2]!.init.body as Blob).text()).toBe('ab')
  expect(ctx.controller.state.parts).toEqual([parts[0]])
})

test('complete 202 retains accepted receipt but is never completed asset state', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  await ctx.controller.sendRemaining()
  await ctx.controller.complete()
  const sent = ctx.requests.at(-1)!
  expect(sent.path).toBe(`/uploads/${uploadId}/complete`)
  expect(JSON.parse(String(sent.init.body))).toEqual({ parts })
  expect(ctx.controller.state.completionReceipt?.validation).toBe('VALIDATING')
  expect(ctx.controller.state.status).toBeNull()
  expect(ctx.controller.state.assetId).toBeNull()
  ctx.handle(() => Response.json(status('COMPLETED')))
  await ctx.controller.refresh()
  expect(ctx.controller.state.assetId).toBe(assetId)
})

test('unknown complete retry uses original parts/key and preserves original accepted response', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  await ctx.controller.sendRemaining()
  ctx.handle(() => {
    throw new TypeError('self-owned lost completion reply')
  })
  await ctx.controller.complete()
  const original = ctx.requests.at(-1)!
  ctx.handle(() => Response.json(status('VALIDATING').result, { status: 202 }))
  await ctx.controller.retry()
  expect(ctx.requests.at(-1)!.init.body).toBe(original.init.body)
  expect(ctx.requests.at(-1)!.init.headers).toEqual(original.init.headers)
  expect(ctx.controller.state.assetId).toBeNull()
})

test.each(['generation', 'membership', 'permission', 'case', 'source', 'unmount'])(
  '%s change clears file context and ignores late create response',
  async (change) => {
    const ctx = await setup()
    await ctx.controller.choose(ctx.file)
    let release!: (response: Response) => void
    ctx.handle(() => new Promise<Response>((resolve) => (release = resolve)))
    const request = ctx.controller.create()
    await vi.waitFor(() => expect(ctx.requests).toHaveLength(1))
    if (change === 'generation') ctx.session.disconnect()
    if (change === 'membership') ctx.session.state.user!.case_ids = []
    if (change === 'permission') ctx.session.state.user!.permissions = ['source.read']
    if (change === 'case') ctx.selection.caseId = otherCase
    if (change === 'source') ctx.selection.source!.version++
    if (change === 'unmount') ctx.controller.dispose()
    release(Response.json(upload))
    await request
    expect(ctx.controller.state.session).toBeNull()
    expect(ctx.controller.state.digest).toBe('')
    expect(ctx.controller.state.busy).toBe(false)
  },
)

test('resume compares all server receipts to retained file bytes before skipping parts', async () => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  await ctx.controller.reconcile()
  expect(ctx.controller.state.parts).toEqual(parts)
  await ctx.controller.sendRemaining()
  expect(ctx.requests.filter((request) => request.init.method === 'PUT')).toHaveLength(0)
})

test.each([
  'hash',
  'length',
  'number',
  'duplicate',
  'cursor-loop',
  'page-version',
  'status-version',
])('resume %s mismatch clears accumulated receipts and never writes', async (fault) => {
  const ctx = await setup()
  await ctx.controller.choose(ctx.file)
  await ctx.controller.create()
  let reads = 0
  ctx.handle((path) => {
    if (!path.includes('/parts?')) {
      reads++
      return Response.json({
        ...status(),
        session: { ...status().session, version: fault === 'status-version' && reads > 1 ? 4 : 3 },
      })
    }
    const rows = parts.map((part) => ({ ...part }))
    if (fault === 'hash') rows[0]!.sha256 = 'a'.repeat(64)
    if (fault === 'length') rows[0]!.size_bytes = 1
    if (fault === 'number') rows[0]!.part_no = 3
    if (fault === 'duplicate') rows.push({ ...rows[0]! })
    return Response.json({
      items: rows,
      next_cursor: fault === 'cursor-loop' ? 'loop' : null,
      session_version: fault === 'page-version' ? 4 : 3,
    })
  })
  await ctx.controller.reconcile()
  expect(ctx.controller.state.parts).toEqual([])
  expect(ctx.controller.state.error).not.toBe('')
  expect(ctx.requests.filter((request) => request.init.method === 'PUT')).toHaveLength(0)
})

test.each(['total', 'upload', 'result', 'asset'])(
  'invalid %s status cannot show an asset',
  async (fault) => {
    const ctx = await setup()
    await ctx.controller.choose(ctx.file)
    await ctx.controller.create()
    const response = status('COMPLETED')
    if (fault === 'total') response.total_size_bytes = 4
    if (fault === 'upload') response.session.upload_id = assetId
    if (fault === 'result') response.result!.validation = 'VALIDATING'
    if (fault === 'asset') response.result!.asset_id = null
    ctx.handle(() => Response.json(response))
    await ctx.controller.refresh()
    expect(ctx.controller.state.status).toBeNull()
    expect(ctx.controller.state.assetId).toBeNull()
    expect(ctx.controller.state.error).not.toBe('')
  },
)
