import { afterEach, expect, test, vi } from 'vitest'
import { BusinessClient, type Schemas } from './api'
import { createAssetCatalog, createAssetReader, createTaskCatalog } from './catalog'

const caseId = '20000000-0000-4000-8000-000000000001'
const otherCaseId = '20000000-0000-4000-8000-000000000002'
const assetId = '30000000-0000-4000-8000-000000000001'
const asset: Schemas['Asset'] = {
  asset_id: assetId,
  case_id: caseId,
  content_id: assetId,
  source_id: assetId,
  kind: 'original',
  object_ref: { object_id: assetId, version_id: 'self-owned-v1', sha256: 'a'.repeat(64) },
  mime: 'image/png',
  size_bytes: 128,
  duration_ms: null,
  width: 10,
  height: 10,
  state: 'VALID',
  version: 1,
  created_at: '2026-10-21T00:00:00Z',
}
function connected(permissions = ['asset.read', 'task.read']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-catalog-token')
  return {
    call: client.call.bind(client),
    has: (permission: string) => permissions.includes(permission),
  }
}
afterEach(() => vi.unstubAllGlobals())

test.each([createAssetCatalog, createTaskCatalog])(
  'missing case and permission never request a global list',
  async (create) => {
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    const catalog = create(connected())
    await catalog.load('')
    expect(catalog.state.error).not.toBe('')
    expect(catalog.state.loaded).toBe(false)
    const denied = create(connected([]))
    await denied.load(caseId)
    expect(denied.state.error).toContain('PERMISSION_REQUIRED')
    expect(fetcher).not.toHaveBeenCalled()
  },
)

test('next page encodes opaque cursor and binds it to case and page size; changed selection restarts', async () => {
  const requested: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    requested.push(url)
    return Response.json({ items: [], next_cursor: 'a+b/c=' })
  })
  const catalog = createAssetCatalog(connected())
  await catalog.load(caseId, 10)
  await catalog.next()
  expect(requested[1]).toBe(
    `/business/api/v1/assets?case_id=${caseId}&limit=10&cursor=a%2Bb%2Fc%3D`,
  )
  expect(catalog.state.pageNumber).toBe(2)
  await catalog.load(otherCaseId, 20)
  expect(requested[2]).toBe(`/business/api/v1/assets?case_id=${otherCaseId}&limit=20`)
  expect(catalog.state.pageNumber).toBe(1)
  catalog.clear()
  await catalog.next()
  expect(requested).toHaveLength(3)
})

test.each([0, 101, 1.5, Number.NaN])(
  'invalid page size %s never reaches the server',
  async (limit) => {
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    const catalog = createTaskCatalog(connected())
    await catalog.load(caseId, limit)
    expect(catalog.state.error).not.toBe('')
    expect(catalog.state.data).toBeNull()
    expect(fetcher).not.toHaveBeenCalled()
  },
)

test('asset catalog rejects cross-case rows and clears earlier data', async () => {
  let wrongCase = false
  vi.stubGlobal('fetch', async () =>
    Response.json({
      items: [{ ...asset, case_id: wrongCase ? otherCaseId : caseId }],
      next_cursor: null,
    }),
  )
  const catalog = createAssetCatalog(connected())
  await catalog.load(caseId)
  expect(catalog.state.data?.items[0]?.object_ref.version_id).toBe('self-owned-v1')
  wrongCase = true
  await catalog.load(caseId)
  expect(catalog.state.data).toBeNull()
  expect(catalog.state.error).not.toBe('')
})

test('task catalog reads current tasks including unavailable results and preserves returned node states', async () => {
  let path = ''
  const task: Schemas['Task'] = {
    task_id: assetId,
    case_id: caseId,
    asset_id: assetId,
    state: 'QUEUED',
    run_version: 1,
    result_version: 0,
    policy_version: 'self-owned-policy',
    version: 1,
    progress: 0,
    nodes: [
      {
        node_code: 'MEDIA',
        state: 'DEFERRED',
        attempt: 1,
        reason: 'RESOURCE_LIMIT',
        required: true,
      },
    ],
    missing_modalities: ['audio'],
    report_eligibility: 'draft_only',
    created_at: asset.created_at,
  }
  vi.stubGlobal('fetch', async (url: string) => {
    path = url
    return Response.json({ items: [task], next_cursor: null })
  })
  const catalog = createTaskCatalog(connected())
  await catalog.load(caseId)
  expect(path).toBe(`/business/api/v1/analysis/tasks?case_id=${caseId}&limit=20`)
  expect(catalog.state.data?.items).toEqual([task])
})

test.each([401, 403, 404, 503])(
  'HTTP %i does not become a successful empty page',
  async (status) => {
    vi.stubGlobal('fetch', async () => Response.json({ code: 'CATALOG_UNAVAILABLE' }, { status }))
    const catalog = createAssetCatalog(connected())
    await catalog.load(caseId)
    expect(catalog.state.loaded).toBe(false)
    expect(catalog.state.data).toBeNull()
    expect(catalog.state.error).toContain('CATALOG_UNAVAILABLE')
  },
)

test('expired cursor drops old rows and cannot be retried as next; first page can recover', async () => {
  const requested: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    requested.push(url)
    return url.includes('cursor=')
      ? Response.json({ code: 'CURSOR_INVALID' }, { status: 422 })
      : Response.json({ items: [asset], next_cursor: 'expired' })
  })
  const catalog = createAssetCatalog(connected())
  await catalog.load(caseId)
  await catalog.next()
  expect(catalog.state.data).toBeNull()
  expect(catalog.state.error).toContain('CURSOR_INVALID')
  await catalog.next()
  expect(requested).toHaveLength(2)
  await catalog.load(caseId)
  expect(catalog.state.pageNumber).toBe(1)
  expect(catalog.state.data?.items).toEqual([asset])
})

test('case change and explicit clear discard an older catalog response', async () => {
  let finish!: (response: Response) => void
  vi.stubGlobal('fetch', async (url: string) =>
    url.includes(caseId)
      ? new Promise<Response>((resolve) => {
          finish = resolve
        })
      : Response.json({ items: [], next_cursor: null }),
  )
  const catalog = createAssetCatalog(connected())
  const old = catalog.load(caseId)
  catalog.clear()
  await catalog.load(otherCaseId)
  finish(Response.json({ items: [asset], next_cursor: 'stale' }))
  await old
  expect(catalog.state.data).toEqual({ items: [], next_cursor: null })
  expect(catalog.state.caseId).toBe(otherCaseId)
})

test('older failed request cannot clear a newer successful page', async () => {
  let finish!: (response: Response) => void
  vi.stubGlobal('fetch', async (url: string) =>
    url.includes(caseId)
      ? new Promise<Response>((resolve) => {
          finish = resolve
        })
      : Response.json({ items: [], next_cursor: 'current-cursor' }),
  )
  const catalog = createTaskCatalog(connected())
  const old = catalog.load(caseId)
  await catalog.load(otherCaseId)
  finish(Response.json({ code: 'CURSOR_INVALID' }, { status: 422 }))
  await old
  expect(catalog.state.error).toBe('')
  expect(catalog.state.loaded).toBe(true)
  expect(catalog.state.data?.next_cursor).toBe('current-cursor')
})

test('asset detail rejects object and case mismatches and discards late selection responses', async () => {
  let result = asset
  vi.stubGlobal('fetch', async () => Response.json(result))
  const detail = createAssetReader(connected())
  await detail.load(caseId, assetId)
  expect(detail.state.data).toEqual(asset)
  result = { ...asset, case_id: otherCaseId }
  await detail.load(caseId, assetId)
  expect(detail.state.data).toBeNull()
  expect(detail.state.error).not.toBe('')
  result = { ...asset, asset_id: otherCaseId }
  await detail.load(caseId, assetId)
  expect(detail.state.data).toBeNull()
  let finish!: (response: Response) => void
  vi.stubGlobal(
    'fetch',
    () =>
      new Promise<Response>((resolve) => {
        finish = resolve
      }),
  )
  const old = detail.load(caseId, assetId)
  detail.clear()
  finish(Response.json(asset))
  await old
  expect(detail.state.data).toBeNull()
  expect(detail.state.loaded).toBe(false)
})
