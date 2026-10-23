import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import type { BusinessSession } from './session'

const caseId = '20000000-0000-4000-8000-000000000001'
const otherId = '20000000-0000-4000-8000-000000000002'
const assetId = '30000000-0000-4000-8000-000000000001'
const sourceId = '40000000-0000-4000-8000-000000000001'
const source: Schemas['Source'] = {
  source_id: sourceId,
  case_id: caseId,
  name: 'self-owned asset source',
  source_type: 'synthetic',
  authorization_ref: 'self-owned-authority/1',
  authorization_status: 'verified',
  purpose: ['upload', 'analysis'],
  expires_at: null,
  version: 2,
}
function asset(): Schemas['Asset'] {
  return {
    asset_id: assetId,
    case_id: caseId,
    source_id: sourceId,
    content_id: otherId,
    kind: 'original',
    object_ref: { object_id: assetId, version_id: 'self-owned/1', sha256: 'a'.repeat(64) },
    mime: 'image/png',
    size_bytes: 64,
    width: 2,
    height: 2,
    duration_ms: null,
    state: 'VALID',
    version: 1,
    created_at: '2026-10-22T00:00:00Z',
  }
}
const active: { dispose: () => void }[] = []
async function setup(permissions = ['asset.read', 'source.read']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-asset-source-token')
  const session = {
    state: reactive({
      generation: 1,
      user: {
        user_id: assetId,
        org_id: otherId,
        roles: ['analyst'],
        permissions,
        case_ids: [caseId],
      } as Schemas['CurrentUser'] | null,
    }),
    call: client.call.bind(client),
    has: (permission: string): boolean =>
      session.state.user?.permissions.includes(permission) ?? false,
  } satisfies Pick<BusinessSession, 'call' | 'has'> & {
    state: Pick<BusinessSession['state'], 'generation' | 'user'>
  }
  const selected = reactive({
    caseId,
    assetId,
    asset: asset() as Schemas['Asset'] | null,
    loaded: true,
    busy: false,
  })
  const load = import.meta.glob<{
    createAssetSourceReader: typeof import('./asset-source').createAssetSourceReader
  }>('./asset-source.ts')['./asset-source.ts']
  expect(load, 'the read-only asset source controller is missing').toBeDefined()
  const reader = (await load!()).createAssetSourceReader(session, () => selected)
  active.push(reader)
  return { session, selected, reader }
}
afterEach(() => {
  active.splice(0).forEach((reader) => reader.dispose())
  vi.unstubAllGlobals()
})

test('reads only the loaded asset source with an exact GET and no case query or mutation', async () => {
  const requests: { url: string; init: RequestInit }[] = []
  vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
    requests.push({ url, init })
    return Response.json(source)
  })
  const { reader, selected } = await setup()
  expect(reader.canLoad()).toBe(true)
  await reader.load()
  expect(reader.state.data).toEqual(source)
  expect(reader.state.loaded).toBe(true)
  expect(requests).toHaveLength(1)
  expect(requests[0]?.url).toBe(`/business/api/v1/sources/${sourceId}`)
  expect(requests[0]?.init.method).toBe('GET')
  expect(requests[0]?.init.body).toBeUndefined()
  expect(selected.asset).toEqual(asset())
})

test.each([{ permissions: [] }, { permissions: ['asset.read'] }, { permissions: ['source.read'] }])(
  'missing permissions refuse without a request: %j',
  async ({ permissions }) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const { reader } = await setup(permissions)
    expect(reader.canLoad()).toBe(false)
    await reader.load()
    expect(reader.state.data).toBeNull()
    expect(reader.state.error).not.toBe('')
    expect(fetch).not.toHaveBeenCalled()
  },
)

test.each([
  'no-user',
  'not-loaded',
  'busy-detail',
  'wrong-asset',
  'wrong-case',
  'hidden-case',
  'no-asset',
  'invalid-source',
])('unbound selection refuses before reading: %s', async (mode) => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  const { reader, selected, session } = await setup()
  if (mode === 'no-user') session.state.user = null
  if (mode === 'not-loaded') selected.loaded = false
  if (mode === 'busy-detail') selected.busy = true
  if (mode === 'wrong-asset') selected.assetId = otherId
  if (mode === 'wrong-case') selected.asset!.case_id = otherId
  if (mode === 'hidden-case') session.state.user!.case_ids = []
  if (mode === 'no-asset') selected.asset = null
  if (mode === 'invalid-source') selected.asset!.source_id = '../not-a-source'
  expect(reader.canLoad()).toBe(false)
  await reader.load()
  expect(reader.state.data).toBeNull()
  expect(fetch).not.toHaveBeenCalled()
})

test.each([
  { source_id: otherId },
  { case_id: otherId },
  { authorization_ref: '' },
  { purpose: [] },
  { version: 0 },
  { authorization_status: 'unknown' },
  { expires_at: 'not-a-time' },
  { unexpected: 'field' },
])('wrong binding or malformed source is never displayed: %j', async (change) => {
  vi.stubGlobal('fetch', async () => Response.json({ ...source, ...change }))
  const { reader } = await setup()
  await reader.load()
  expect(reader.state.data).toBeNull()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.error).not.toBe('')
})

test.each(['pending', 'verified', 'expired', 'revoked'] as const)(
  'displays the reported %s status without changing asset eligibility',
  async (status) => {
    vi.stubGlobal('fetch', async () => Response.json({ ...source, authorization_status: status }))
    const { reader, selected } = await setup()
    await reader.load()
    expect(reader.state.data?.authorization_status).toBe(status)
    expect(reader.state.data?.expires_at).toBeNull()
    expect(selected.asset?.state).toBe('VALID')
  },
)

test.each([403, 404, 503])(
  'a %s refresh clears old detail and preserves safe retry',
  async (status) => {
    let calls = 0
    vi.stubGlobal('fetch', async () => {
      calls++
      return calls === 2
        ? Response.json({ detail: 'private upstream URL and authority error' }, { status })
        : Response.json(source)
    })
    const { reader } = await setup()
    await reader.load()
    expect(reader.state.data).not.toBeNull()
    await reader.load()
    expect(reader.state.data).toBeNull()
    expect(reader.state.loaded).toBe(false)
    expect(reader.state.error).not.toContain('private upstream')
    await reader.load()
    expect(reader.state.loaded).toBe(true)
  },
)

test.each([
  'asset',
  'source',
  'case',
  'detail-reload',
  'asset-version',
  'generation',
  'user',
  'org',
  'role',
  'permission',
  'case-membership',
  'dispose',
])('a late source response cannot restore changed context: %s', async (mode) => {
  let complete!: (response: Response) => void
  vi.stubGlobal(
    'fetch',
    () =>
      new Promise<Response>((resolve) => {
        complete = resolve
      }),
  )
  const { reader, selected, session } = await setup()
  const pending = reader.load()
  expect(reader.state.busy).toBe(true)
  if (mode === 'asset') {
    selected.assetId = otherId
    selected.asset!.asset_id = otherId
  }
  if (mode === 'source') selected.asset!.source_id = otherId
  if (mode === 'case') selected.caseId = otherId
  if (mode === 'detail-reload') selected.busy = true
  if (mode === 'asset-version') selected.asset!.version++
  if (mode === 'generation') session.state.generation++
  if (mode === 'user') session.state.user!.user_id = otherId
  if (mode === 'org') session.state.user!.org_id = assetId
  if (mode === 'role') session.state.user!.roles = ['auditor']
  if (mode === 'permission') session.state.user!.permissions = ['asset.read']
  if (mode === 'case-membership') session.state.user!.case_ids = []
  if (mode === 'dispose') reader.dispose()
  expect(reader.state.data).toBeNull()
  complete(Response.json(source))
  await pending
  expect(reader.state.data).toBeNull()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.busy).toBe(false)
})

test('clears an already displayed record on same-generation role changes and disposal prevents reads', async () => {
  const fetch = vi.fn(async () => Response.json(source))
  vi.stubGlobal('fetch', fetch)
  const { reader, session } = await setup()
  await reader.load()
  expect(reader.state.data).not.toBeNull()
  session.state.user!.roles.push('reviewer')
  expect(reader.state.data).toBeNull()
  reader.dispose()
  await reader.load()
  expect(reader.canLoad()).toBe(false)
  expect(fetch).toHaveBeenCalledTimes(1)
})
