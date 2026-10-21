import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import type { BusinessSession } from './session'

type ReadSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
const active: { dispose: () => void }[] = []
const modelId = '30000000-0000-4000-8000-000000000001'
const model: Schemas['Model'] = {
  model_id: modelId,
  name: 'self-owned model metadata',
  version: 'synthetic/1',
  capability: 'media.ocr',
  digest: 'a'.repeat(64),
  dataset_version: 'self-owned-data/1',
  model_card_ref: 'controlled-card/1',
  license_record_ref: 'controlled-license/1',
  backend: 'onnxruntime',
  environment_ref: 'controlled-environment/1',
  status: 'REGISTERED',
  row_version: 1,
}
const evaluation: Schemas['Evaluation'] = {
  evaluation_id: '40000000-0000-4000-8000-000000000001',
  model_id: modelId,
  dataset_id: 'self-owned-data',
  dataset_version: 'self-owned-data/1',
  protocol_id: 'self-owned-protocol/1',
  split: 'validation',
  sample_count: 3,
  failure_count: 1,
  metrics: {
    macro_f1: null,
    recall: 0,
    iou: null,
    recall_at_k: null,
    ece: null,
    boundary_mae_ms: null,
  },
  artifact_ref: { object_id: modelId, version_id: 'immutable/1', sha256: 'b'.repeat(64) },
  created_at: '2026-10-21T00:00:00Z',
}

function connected(permissions = ['model.read']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-model-token')
  const state = reactive({
    generation: 1,
    user: {
      user_id: '10000000-0000-4000-8000-000000000001',
      org_id: '20000000-0000-4000-8000-000000000001',
      roles: ['algorithm_admin'],
      permissions,
      case_ids: [],
    } as Schemas['CurrentUser'] | null,
  })
  return {
    call: client.call.bind(client),
    has: (permission: string) => state.user?.permissions.includes(permission) ?? false,
    state,
  }
}

async function reader(session: ReadSession) {
  const load = import.meta.glob<{
    createModelsReader: typeof import('./models').createModelsReader
  }>('./models.ts')['./models.ts']
  expect(load, 'the current-organization model reader is missing').toBeDefined()
  const result = (await load!()).createModelsReader(session)
  active.push(result)
  return result
}

afterEach(() => {
  active.splice(0).forEach((item) => item.dispose())
  vi.unstubAllGlobals()
})

test('identity switching immediately clears both lists and discards late responses', async () => {
  const session = connected()
  const catalog = await reader(session)
  vi.stubGlobal('fetch', async () => Response.json({ items: [model], next_cursor: null }))
  await catalog.models.load()
  expect(catalog.models.state.data?.items).toEqual([model])
  let release!: (response: Response) => void
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
  const pending = catalog.evaluations.load()
  session.state.user = null
  session.state.generation++
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.evaluations.state.data).toBeNull()
  expect(catalog.evaluations.state.busy).toBe(false)
  release(Response.json({ items: [evaluation], next_cursor: 'old-identity-cursor' }))
  await pending
  expect(catalog.evaluations.state.loaded).toBe(false)
  expect(catalog.evaluations.state.data).toBeNull()
  expect(catalog.evaluations.state.error).toBe('')
})

test('a superseded request error cannot replace a newer successful page', async () => {
  const catalog = await reader(connected())
  let release!: (response: Response) => void
  vi.stubGlobal('fetch', (url: string) =>
    url.includes('limit=10')
      ? new Promise<Response>((resolve) => (release = resolve))
      : Promise.resolve(Response.json({ items: [model], next_cursor: 'current' })),
  )
  const old = catalog.models.load(10)
  await catalog.models.load(20)
  release(Response.json({ code: 'CONDITIONAL_FACTS_UNAVAILABLE' }, { status: 503 }))
  await old
  expect(catalog.models.state.data?.items).toEqual([model])
  expect(catalog.models.state.data?.next_cursor).toBe('current')
  expect(catalog.models.state.error).toBe('')
  expect(catalog.models.state.busy).toBe(false)
})

test('disposing clears results and prevents pending completion or later loads', async () => {
  const catalog = await reader(connected())
  let release!: (response: Response) => void
  const fetcher = vi.fn(() => new Promise<Response>((resolve) => (release = resolve)))
  vi.stubGlobal('fetch', fetcher)
  const pending = catalog.models.load()
  catalog.dispose()
  release(Response.json({ items: [model], next_cursor: null }))
  await pending
  await catalog.models.load()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.models.state.loaded).toBe(false)
})

test('missing identity or model.read permission never starts a list request', async () => {
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  const session = connected([])
  const catalog = await reader(session)
  await catalog.models.load()
  await catalog.evaluations.load()
  expect(catalog.models.state.error).toContain('PERMISSION_REQUIRED')
  expect(catalog.evaluations.state.error).toContain('PERMISSION_REQUIRED')
  session.state.user = null
  session.state.generation++
  await catalog.models.load()
  expect(catalog.models.state.error).toContain('AUTHENTICATION_REQUIRED')
  expect(fetcher).not.toHaveBeenCalled()
})

test('pagination remains independent and sends only limit and the opaque cursor', async () => {
  const requested: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    requested.push(url)
    return url.includes('/model-evaluations')
      ? Response.json({ items: [evaluation], next_cursor: 'evaluation+/' })
      : Response.json({ items: [model], next_cursor: 'model+/' })
  })
  const catalog = await reader(connected())
  await catalog.models.load(10)
  await catalog.evaluations.load(20)
  await catalog.models.next()
  await catalog.evaluations.next()
  expect(requested).toEqual([
    '/business/api/v1/models?limit=10',
    '/business/api/v1/model-evaluations?limit=20',
    '/business/api/v1/models?limit=10&cursor=model%2B%2F',
    '/business/api/v1/model-evaluations?limit=20&cursor=evaluation%2B%2F',
  ])
  expect(catalog.models.state.pageNumber).toBe(2)
  expect(catalog.evaluations.state.pageNumber).toBe(2)
  await catalog.models.load(50)
  expect(requested.at(-1)).toBe('/business/api/v1/models?limit=50')
  expect(catalog.models.state.pageNumber).toBe(1)
  expect(catalog.evaluations.state.pageNumber).toBe(2)
})

test.each([401, 403, 503])(
  'HTTP %i clears old data without becoming an empty success',
  async (status) => {
    const catalog = await reader(connected())
    vi.stubGlobal('fetch', async () => Response.json({ items: [model], next_cursor: null }))
    await catalog.models.load()
    vi.stubGlobal('fetch', async () =>
      Response.json({ code: 'MODEL_METADATA_UNAVAILABLE' }, { status }),
    )
    await catalog.models.load()
    expect(catalog.models.state.data).toBeNull()
    expect(catalog.models.state.loaded).toBe(false)
    expect(catalog.models.state.error).toContain('MODEL_METADATA_UNAVAILABLE')
  },
)

test('an invalid cursor removes old rows and requires an explicit first-page reload', async () => {
  const requested: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    requested.push(url)
    return url.includes('cursor=')
      ? Response.json({ code: 'PAGE_CURSOR_INVALID' }, { status: 422 })
      : Response.json({ items: [model], next_cursor: 'expired' })
  })
  const catalog = await reader(connected())
  await catalog.models.load()
  await catalog.models.next()
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.models.state.pageNumber).toBe(0)
  expect(catalog.models.state.error).toContain('PAGE_CURSOR_INVALID')
  await catalog.models.next()
  expect(requested).toHaveLength(2)
  await catalog.models.load()
  expect(catalog.models.state.pageNumber).toBe(1)
})

test('permission removal before next-page navigation cannot reuse the prior cursor', async () => {
  const session = connected()
  const catalog = await reader(session)
  const fetcher = vi.fn(async () => Response.json({ items: [model], next_cursor: 'not-a-grant' }))
  vi.stubGlobal('fetch', fetcher)
  await catalog.models.load()
  session.state.user!.permissions.length = 0
  await catalog.models.next()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.models.state.error).toBe('')
  await catalog.models.load()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(catalog.models.state.error).toContain('PERMISSION_REQUIRED')
})

test('same-identity permission revocation immediately clears both loaded pages and cursors', async () => {
  const session = connected()
  const catalog = await reader(session)
  const fetcher = vi.fn(async (url: string) =>
    Response.json({
      items: url.includes('/model-evaluations') ? [evaluation] : [model],
      next_cursor: 'not-a-grant',
    }),
  )
  vi.stubGlobal('fetch', fetcher)
  await catalog.models.load()
  await catalog.evaluations.load()
  expect(catalog.models.state.data?.items).toEqual([model])
  expect(catalog.evaluations.state.data?.items).toEqual([evaluation])
  const generation = session.state.generation
  session.state.user!.permissions.length = 0
  expect(session.state.generation).toBe(generation)
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.evaluations.state.data).toBeNull()
  expect(catalog.models.state.pageNumber).toBe(0)
  expect(catalog.evaluations.state.pageNumber).toBe(0)
  expect(fetcher).toHaveBeenCalledTimes(2)
})

test.each(['models', 'evaluations'] as const)(
  'permission revocation during a pending %s request synchronously invalidates both pages',
  async (kind) => {
    const session = connected()
    const catalog = await reader(session)
    vi.stubGlobal('fetch', async (url: string) =>
      Response.json({
        items: url.includes('/model-evaluations') ? [evaluation] : [model],
        next_cursor: null,
      }),
    )
    await catalog.models.load()
    await catalog.evaluations.load()
    let release!: (response: Response) => void
    vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
    const pending = catalog[kind].load()
    session.state.user!.permissions.length = 0
    const immediately = {
      models: catalog.models.state.data,
      evaluations: catalog.evaluations.state.data,
      busy: catalog[kind].state.busy,
    }
    release(
      Response.json({ items: kind === 'models' ? [model] : [evaluation], next_cursor: 'late' }),
    )
    await pending
    expect(immediately).toEqual({ models: null, evaluations: null, busy: false })
    expect(catalog.models.state.data).toBeNull()
    expect(catalog.evaluations.state.data).toBeNull()
    expect(catalog[kind].state.error).toBe('')
    expect(catalog[kind].state.loaded).toBe(false)
  },
)

test.each([0, 101, 1.5, Number.NaN])('invalid page size %s never requests', async (limit) => {
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  const catalog = await reader(connected())
  await catalog.models.load(limit)
  expect(fetcher).not.toHaveBeenCalled()
  expect(catalog.models.state.error).not.toBe('')
})

test.each([
  { items: null, next_cursor: null },
  { items: [null], next_cursor: null },
  { items: [{ model_id: modelId }], next_cursor: null },
  { items: [], next_cursor: '' },
  { items: [], next_cursor: 123 },
])('malformed list response is refused: %j', async (data) => {
  const catalog = await reader(connected())
  vi.stubGlobal('fetch', async () => Response.json(data))
  await catalog.models.load()
  expect(catalog.models.state.data).toBeNull()
  expect(catalog.models.state.loaded).toBe(false)
  expect(catalog.models.state.error).not.toBe('')
})

test('evaluation metadata preserves unknown metrics, actual zero values and fixed references', async () => {
  const catalog = await reader(connected())
  vi.stubGlobal('fetch', async () => Response.json({ items: [evaluation], next_cursor: null }))
  await catalog.evaluations.load()
  expect(catalog.evaluations.state.data?.items[0]?.metrics.macro_f1).toBeNull()
  expect(catalog.evaluations.state.data?.items[0]?.metrics.recall).toBe(0)
  expect(catalog.evaluations.state.data?.items[0]?.artifact_ref).toEqual(evaluation.artifact_ref)
  expect(catalog.evaluations.state.data?.items[0]?.sample_count).toBe(3)
  expect(catalog.evaluations.state.data?.items[0]?.failure_count).toBe(1)
})

test.each([
  { ...evaluation, metrics: null },
  { ...evaluation, metrics: { recall: 0 } },
  { ...evaluation, artifact_ref: null },
  { ...evaluation, model_id: 'not-a-model-id' },
  { ...evaluation, failure_count: 4 },
])('incomplete evaluation metadata never reaches the rendered table: %j', async (item) => {
  const catalog = await reader(connected())
  vi.stubGlobal('fetch', async () => Response.json({ items: [item], next_cursor: null }))
  await catalog.evaluations.load()
  expect(catalog.evaluations.state.data).toBeNull()
  expect(catalog.evaluations.state.loaded).toBe(false)
  expect(catalog.evaluations.state.error).not.toBe('')
})
