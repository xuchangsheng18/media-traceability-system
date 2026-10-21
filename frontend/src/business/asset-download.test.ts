import { afterEach, expect, test, vi } from 'vitest'
import { ApiError } from '../api'
import { BusinessClient, type Schemas } from './api'
import { createAssetDownload } from './asset-download'

const caseId = '20000000-0000-4000-8000-000000000001'
const assetId = '30000000-0000-4000-8000-000000000001'
const bytes = new TextEncoder().encode('self-owned download bytes')
async function sha(data: BufferSource) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('')
}
async function fixture() {
  const asset: Schemas['Asset'] = {
    asset_id: assetId,
    case_id: caseId,
    content_id: assetId,
    source_id: assetId,
    kind: 'original',
    object_ref: { object_id: assetId, version_id: 'fixed-v1', sha256: await sha(bytes) },
    mime: 'application/octet-stream',
    size_bytes: bytes.length,
    duration_ms: null,
    width: null,
    height: null,
    state: 'VALID',
    version: 1,
    created_at: '2026-10-21T00:00:00Z',
  }
  const client = new BusinessClient()
  client.replaceToken('self-owned-download-token')
  const permissions = ['asset.download']
  const session = {
    call: client.call.bind(client),
    has: (permission: string) => permissions.includes(permission),
    state: { generation: 1 },
  }
  const selection = { caseId, assetId, asset, loaded: true, busy: false }
  const save = vi.fn()
  const controller = createAssetDownload(session, () => selection, save)
  async function tag() {
    return (
      '"' +
      (await sha(
        new TextEncoder().encode(
          JSON.stringify([
            asset.object_ref.object_id,
            asset.object_ref.version_id,
            asset.object_ref.sha256,
          ]),
        ),
      )) +
      '"'
    )
  }
  return { asset, permissions, session, selection, save, controller, tag }
}
afterEach(() => vi.unstubAllGlobals())

test('verified full download uses existing binary call and UUID-only filename', async () => {
  const ctx = await fixture()
  const etag = await ctx.tag()
  const fetcher = vi.fn(async (_url: string) => new Response(bytes, { headers: { ETag: etag } }))
  vi.stubGlobal('fetch', fetcher)
  expect(ctx.controller.canDownload()).toBe(true)
  await ctx.controller.download()
  expect(fetcher.mock.calls[0]?.[0]).toBe(`/business/api/v1/assets/${assetId}/content`)
  expect(ctx.save).toHaveBeenCalledOnce()
  expect(ctx.save.mock.calls[0]?.[1]).toBe(`asset-${assetId}.bin`)
  expect(ctx.controller.state.message).toContain('已核验')
  expect(ctx.controller.state.busy).toBe(false)
})

test.each(['permission', 'unloaded', 'loading', 'state', 'case', 'asset', 'size', 'digest'])(
  'invalid download selection %s never requests or saves content',
  async (defect) => {
    const ctx = await fixture()
    if (defect === 'permission') ctx.permissions.length = 0
    if (defect === 'unloaded') ctx.selection.loaded = false
    if (defect === 'loading') ctx.selection.busy = true
    if (defect === 'state') ctx.asset.state = 'QUARANTINED'
    if (defect === 'case') ctx.selection.caseId = assetId
    if (defect === 'asset') ctx.selection.assetId = caseId
    if (defect === 'size') ctx.asset.size_bytes = -1
    if (defect === 'digest') ctx.asset.object_ref.sha256 = 'bad'
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    expect(ctx.controller.canDownload()).toBe(false)
    await ctx.controller.download()
    expect(fetcher).not.toHaveBeenCalled()
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.state.error).not.toBe('')
  },
)

test.each(['size', 'hash', 'etag', 'missing-etag'])(
  'size/hash/fixed-version mismatch %s prevents saving',
  async (defect) => {
    const ctx = await fixture()
    const etag = await ctx.tag()
    vi.stubGlobal(
      'fetch',
      async () =>
        new Response(
          defect === 'size'
            ? bytes.slice(1)
            : defect === 'hash'
              ? new Uint8Array(bytes.length)
              : bytes,
          {
            headers:
              defect === 'missing-etag' ? {} : { ETag: defect === 'etag' ? '"wrong"' : etag },
          },
        ),
    )
    await ctx.controller.download()
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.state.error).toContain('核验')
    expect(ctx.controller.state.message).toBe('')
  },
)

test.each(['clear', 'identity', 'case', 'asset', 'detail', 'permission'])(
  'late binary response after %s change cannot save or report success',
  async (change) => {
    const ctx = await fixture()
    const etag = await ctx.tag()
    let release!: (response: Response) => void
    vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
    const pending = ctx.controller.download()
    if (change === 'clear') ctx.controller.clear()
    if (change === 'identity') ctx.session.state.generation++
    if (change === 'case') ctx.selection.caseId = assetId
    if (change === 'asset') ctx.selection.assetId = caseId
    if (change === 'detail') ctx.asset.version++
    if (change === 'permission') ctx.permissions.length = 0
    release(new Response(bytes, { headers: { ETag: etag } }))
    await pending
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.state.message).toBe('')
    expect(ctx.controller.state.busy).toBe(false)
  },
)

test.each([401, 403, 404, 503])(
  'HTTP %i follows shared errors without fake download',
  async (status) => {
    const ctx = await fixture()
    vi.stubGlobal('fetch', async () =>
      Response.json({ code: 'IDENTITY_AUTHORITY_UNAVAILABLE' }, { status }),
    )
    await ctx.controller.download()
    expect(ctx.controller.state.error).toContain('IDENTITY_AUTHORITY_UNAVAILABLE')
    expect(ctx.save).not.toHaveBeenCalled()
  },
)

test('repeat download while pending does not duplicate requests', async () => {
  const ctx = await fixture()
  const etag = await ctx.tag()
  let release!: (response: Response) => void
  const fetcher = vi.fn(() => new Promise<Response>((resolve) => (release = resolve)))
  vi.stubGlobal('fetch', fetcher)
  const pending = ctx.controller.download()
  await ctx.controller.download()
  expect(fetcher).toHaveBeenCalledOnce()
  release(new Response(bytes, { headers: { ETag: etag } }))
  await pending
  expect(ctx.save).toHaveBeenCalledOnce()
})

test('late error after clear cannot overwrite a new selection', async () => {
  const ctx = await fixture()
  let reject!: (error: Error) => void
  ctx.session.call = () => new Promise((_, fail) => (reject = fail))
  const pending = ctx.controller.download()
  ctx.controller.clear()
  reject(new ApiError(503, 'DEPENDENCY_UNAVAILABLE'))
  await pending
  expect(ctx.controller.state.error).toBe('')
})

test('clearing while Blob bytes are pending prevents save after integrity work', async () => {
  const ctx = await fixture()
  const blob = new Blob([bytes])
  let release!: (value: ArrayBuffer) => void
  let started!: () => void
  const observed = new Promise<void>((resolve) => (started = resolve))
  vi.spyOn(blob, 'arrayBuffer').mockImplementation(() => {
    started()
    return new Promise<ArrayBuffer>((resolve) => (release = resolve))
  })
  const response = new Response(bytes, { headers: { ETag: await ctx.tag() } })
  vi.spyOn(response, 'blob').mockResolvedValue(blob)
  vi.stubGlobal('fetch', async () => response)
  const pending = ctx.controller.download()
  await observed
  ctx.controller.clear()
  release(bytes.buffer)
  await pending
  expect(ctx.save).not.toHaveBeenCalled()
  expect(ctx.controller.state.message).toBe('')
})

test('fixed-version ETag matches backend ASCII escaping including surrogate pairs', async () => {
  const ctx = await fixture()
  ctx.asset.object_ref.version_id = '版本🔒'
  const encoded = `["${assetId}","\\u7248\\u672c\\ud83d\\udd12","${ctx.asset.object_ref.sha256}"]`
  const etag = '"' + (await sha(new TextEncoder().encode(encoded))) + '"'
  vi.stubGlobal('fetch', async () => new Response(bytes, { headers: { ETag: etag } }))
  await ctx.controller.download()
  expect(ctx.save).toHaveBeenCalledOnce()
})
