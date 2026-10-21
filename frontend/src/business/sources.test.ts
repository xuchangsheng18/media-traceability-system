import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import type { BusinessSession } from './session'

type SourceSession = Pick<BusinessSession, 'call' | 'has'> & {
  state: Pick<BusinessSession['state'], 'generation' | 'user'>
}
const caseId = '20000000-0000-4000-8000-000000000001'
const otherCase = '20000000-0000-4000-8000-000000000002'
const sourceId = '30000000-0000-4000-8000-000000000001'
const payload: Schemas['SourceCreate'] = {
  case_id: caseId,
  name: 'self-owned registration',
  source_type: 'synthetic',
  authorization_ref: 'self-owned-authority/1',
  purpose: ['upload', 'analysis'],
  expires_at: '2026-11-21T08:00:00.123456+08:00',
}
const source: Schemas['Source'] = {
  ...payload,
  expires_at: '2026-11-21T00:00:00.123456Z',
  source_id: sourceId,
  authorization_status: 'pending',
  version: 1,
}
const active: { dispose: () => void }[] = []

async function setup(permissions = ['source.read', 'source.manage']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-source-token')
  const session: SourceSession = {
    call: client.call.bind(client),
    state: reactive({
      generation: 1,
      user: {
        user_id: '10000000-0000-4000-8000-000000000001',
        org_id: '10000000-0000-4000-8000-000000000002',
        roles: ['data_admin'],
        permissions,
        case_ids: [caseId, otherCase],
      } as Schemas['CurrentUser'] | null,
    }),
    has: (permission) => session.state.user?.permissions.includes(permission) ?? false,
  }
  const selection = reactive({ caseId })
  const draft = reactive({ ...payload, purpose: [...payload.purpose] })
  const load = import.meta.glob<{ createSources: typeof import('./sources').createSources }>(
    './sources.ts',
  )['./sources.ts']
  expect(load, 'the source registration controller is missing').toBeDefined()
  const controller = (await load!()).createSources(
    session,
    () => selection.caseId,
    () => draft,
  )
  active.push(controller)
  return { session, selection, draft, controller }
}

afterEach(() => {
  active.splice(0).forEach((item) => item.dispose())
  vi.unstubAllGlobals()
})

test('unknown network result retries the original immutable payload and idempotency key', async () => {
  const ctx = await setup()
  const requests: RequestInit[] = []
  vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
    requests.push(init)
    if (requests.length === 1) throw new TypeError('self-owned simulated network interruption')
    return Response.json(source, { status: 201, headers: { ETag: '"source-version"' } })
  })
  await ctx.controller.registration.submit()
  expect(ctx.controller.registration.state.uncertain).toBe(true)
  expect(ctx.controller.registration.state.data).toBeNull()
  await ctx.controller.registration.retry()
  expect(requests).toHaveLength(2)
  expect(requests[0]?.body).toBe(requests[1]?.body)
  expect(requests[0]?.headers).toEqual(requests[1]?.headers)
  const headers = requests[0]?.headers as Record<string, string>
  expect(headers['Idempotency-Key']).toMatch(/^[a-f0-9-]{36}$/)
  expect(headers['If-Match']).toBeUndefined()
  expect(JSON.parse(String(requests[0]?.body))).toEqual(payload)
  expect(ctx.controller.registration.state.data).toEqual(source)
  expect(ctx.controller.registration.state.uncertain).toBe(false)
  expect(ctx.controller.registration.state.message).toContain('pending')
  expect(ctx.controller.registration.state.message).toContain('尚不能作为有效用途授权')
})

const retryRejections = [
  { status: 409, code: 'SOURCE_VERSION_CONFLICT' },
  { status: 403, code: 'SOURCE_AUTHORIZATION_REQUIRED' },
  { status: 422, code: 'INVALID_SOURCE_REGISTRATION' },
]

test.each(
  ['network', '503'].flatMap((first) =>
    retryRejections.map((rejection) => ({ first, ...rejection })),
  ),
)(
  'an initial $first result remains uncertain after retry HTTP $status and retains the original intent',
  async ({ first, status, code }) => {
    const ctx = await setup()
    const requests: RequestInit[] = []
    vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
      requests.push(init)
      if (requests.length === 1) {
        if (first === 'network') throw new TypeError('self-owned unknown network result')
        return Response.json({ code: 'SOURCE_SYNCHRONIZATION_UNAVAILABLE' }, { status: 503 })
      }
      if (requests.length === 2) return Response.json({ code }, { status })
      return Response.json(source, { status: 201 })
    })
    await ctx.controller.registration.submit()
    expect(ctx.controller.registration.state.uncertain).toBe(true)
    await ctx.controller.registration.retry()
    expect(ctx.controller.registration.state.error).toContain(code)
    expect(ctx.controller.registration.state.uncertain).toBe(true)
    expect(ctx.controller.registration.state.data).toBeNull()
    expect(ctx.controller.registration.state.message).toBe('')
    await ctx.controller.registration.submit()
    expect(requests).toHaveLength(2)
    ctx.draft.name = 'edited unresolved intent'
    await ctx.controller.registration.submit()
    await ctx.controller.registration.retry()
    expect(requests).toHaveLength(2)
    ctx.draft.name = payload.name
    await ctx.controller.registration.retry()
    expect(requests).toHaveLength(3)
    for (const request of requests) {
      expect(request.body).toBe(requests[0]?.body)
      expect(request.headers).toEqual(requests[0]?.headers)
    }
    expect(ctx.controller.registration.state.data).toEqual(source)
    expect(ctx.controller.registration.state.uncertain).toBe(false)
  },
)

test.each(retryRejections)(
  'a first definitive HTTP $status failure allows a new registration intent',
  async ({ status, code }) => {
    const ctx = await setup()
    const requests: RequestInit[] = []
    vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
      requests.push(init)
      if (requests.length === 1) return Response.json({ code }, { status })
      return Response.json(source, { status: 201 })
    })
    await ctx.controller.registration.submit()
    expect(ctx.controller.registration.state.error).toContain(code)
    expect(ctx.controller.registration.state.uncertain).toBe(false)
    await ctx.controller.registration.submit()
    expect(requests).toHaveLength(2)
    expect(requests[1]?.headers).not.toEqual(requests[0]?.headers)
    expect(ctx.controller.registration.state.data).toEqual(source)
  },
)

test('editing an unresolved payload cannot resend it with the old key or replace the old intent', async () => {
  const ctx = await setup()
  const requests: RequestInit[] = []
  vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
    requests.push(init)
    if (requests.length === 1) throw new TypeError('network result unknown')
    return Response.json(source, { status: 201 })
  })
  await ctx.controller.registration.submit()
  ctx.draft.name = 'edited but not submitted'
  await ctx.controller.registration.submit()
  await ctx.controller.registration.retry()
  expect(requests).toHaveLength(1)
  expect(ctx.controller.registration.state.uncertain).toBe(true)
  expect(ctx.controller.registration.state.data).toBeNull()
  ctx.draft.name = payload.name
  await ctx.controller.registration.retry()
  expect(requests).toHaveLength(2)
  expect(requests[1]?.body).toBe(requests[0]?.body)
  expect(requests[1]?.headers).toEqual(requests[0]?.headers)
})

test.each(['case', 'identity', 'user', 'organization', 'edit', 'permission', 'dispose'])(
  'late registration success after %s change cannot display or replay old results',
  async (change) => {
    const ctx = await setup()
    let release!: (response: Response) => void
    const fetcher = vi.fn(() => new Promise<Response>((resolve) => (release = resolve)))
    vi.stubGlobal('fetch', fetcher)
    const pending = ctx.controller.registration.submit()
    if (change === 'case') ctx.selection.caseId = otherCase
    if (change === 'identity') ctx.session.state.generation++
    if (change === 'user') ctx.session.state.user!.user_id = '10000000-0000-4000-8000-000000000003'
    if (change === 'organization')
      ctx.session.state.user!.org_id = '10000000-0000-4000-8000-000000000004'
    if (change === 'edit') ctx.draft.name = 'new draft'
    if (change === 'permission') ctx.session.state.user!.permissions = ['source.read']
    if (change === 'dispose') ctx.controller.dispose()
    release(Response.json(source, { status: 201 }))
    await pending
    expect(ctx.controller.registration.state.data).toBeNull()
    expect(ctx.controller.registration.state.message).toBe('')
    expect(ctx.controller.registration.state.busy).toBe(false)
    await ctx.controller.registration.retry()
    expect(fetcher).toHaveBeenCalledOnce()
  },
)

test('repeat submit while pending never starts a second mutation', async () => {
  const ctx = await setup()
  let release!: (response: Response) => void
  const fetcher = vi.fn(() => new Promise<Response>((resolve) => (release = resolve)))
  vi.stubGlobal('fetch', fetcher)
  const pending = ctx.controller.registration.submit()
  await ctx.controller.registration.submit()
  expect(fetcher).toHaveBeenCalledOnce()
  release(Response.json(source, { status: 201 }))
  await pending
  expect(ctx.controller.registration.state.data).toEqual(source)
})

test.each([
  'case_id',
  'name',
  'source_type',
  'authorization_ref',
  'purpose',
  'expires_at',
  'source_id',
  'version',
  'authorization_status',
])('201 with an invalid or mismatched %s never becomes registration success', async (field) => {
  const ctx = await setup()
  const values: Record<string, unknown> = {
    case_id: otherCase,
    name: 'unrelated source name',
    source_type: 'public_licensed',
    authorization_ref: 'different authorization',
    purpose: ['training'],
    expires_at: '2026-11-21T00:00:00.123457Z',
    source_id: 'invalid-id',
    version: 0,
    authorization_status: 'revoked',
  }
  vi.stubGlobal('fetch', async () =>
    Response.json({ ...source, [field]: values[field] }, { status: 201 }),
  )
  await ctx.controller.registration.submit()
  expect(ctx.controller.registration.state.data).toBeNull()
  expect(ctx.controller.registration.state.message).toBe('')
  expect(ctx.controller.registration.state.error).not.toBe('')
  expect(ctx.controller.registration.state.uncertain).toBe(true)
})

test.each([401, 403, 404, 409, 422, 503])(
  'HTTP %i is an explicit failure without a fake source',
  async (status) => {
    const ctx = await setup()
    vi.stubGlobal('fetch', async () =>
      Response.json({ code: 'SOURCE_AUTHORIZATION_REQUIRED' }, { status }),
    )
    await ctx.controller.registration.submit()
    expect(ctx.controller.registration.state.data).toBeNull()
    expect(ctx.controller.registration.state.error).toContain('SOURCE_AUTHORIZATION_REQUIRED')
    expect(ctx.controller.registration.state.message).toBe('')
    expect(ctx.controller.registration.state.uncertain).toBe(status === 503)
  },
)

test.each(['authorization_status', 'version', 'org_id', 'created_by'])(
  'client authority field %s is rejected before a request',
  async (field) => {
    const ctx = await setup()
    Object.assign(ctx.draft, { [field]: 'forged' })
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.registration.submit()
    expect(fetcher).not.toHaveBeenCalled()
    expect(ctx.controller.registration.state.error).not.toBe('')
  },
)

test('source.read and source.manage independently guard reads and registration', async () => {
  const read = await setup(['source.read'])
  const fetcher = vi.fn(async () => Response.json({ items: [source], next_cursor: null }))
  vi.stubGlobal('fetch', fetcher)
  await read.controller.list.load()
  await read.controller.registration.submit()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(read.controller.list.state.data?.items).toEqual([source])
  expect(read.controller.registration.state.error).toContain('PERMISSION_REQUIRED')
  const write = await setup(['source.manage'])
  vi.stubGlobal('fetch', async () => Response.json(source, { status: 201 }))
  await write.controller.list.load()
  await write.controller.registration.submit()
  expect(write.controller.list.state.error).toContain('PERMISSION_REQUIRED')
  expect(write.controller.registration.state.data).toEqual(source)
})

test('source pagination binds only the selected case, size and opaque cursor', async () => {
  const ctx = await setup()
  const requested: string[] = []
  vi.stubGlobal('fetch', async (url: string) => {
    requested.push(url)
    return Response.json({ items: [source], next_cursor: 'a+b/' })
  })
  await ctx.controller.list.load(10)
  await ctx.controller.list.next()
  expect(requested).toEqual([
    `/business/api/v1/sources?case_id=${caseId}&limit=10`,
    `/business/api/v1/sources?case_id=${caseId}&limit=10&cursor=a%2Bb%2F`,
  ])
  expect(ctx.controller.list.state.pageNumber).toBe(2)
  ctx.selection.caseId = otherCase
  expect(ctx.controller.list.state.data).toBeNull()
  await ctx.controller.list.next()
  expect(requested).toHaveLength(2)
})

test('detail and list refuse wrong-case rows; stale case responses cannot restore data', async () => {
  const ctx = await setup()
  vi.stubGlobal('fetch', async () => Response.json({ ...source, case_id: otherCase }))
  await ctx.controller.detail.load(sourceId)
  expect(ctx.controller.detail.state.data).toBeNull()
  expect(ctx.controller.detail.state.error).not.toBe('')
  vi.stubGlobal('fetch', async () =>
    Response.json({ items: [{ ...source, case_id: otherCase }], next_cursor: null }),
  )
  await ctx.controller.list.load()
  expect(ctx.controller.list.state.data).toBeNull()
  let release!: (response: Response) => void
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
  const pending = ctx.controller.detail.load(sourceId)
  ctx.selection.caseId = otherCase
  release(Response.json(source))
  await pending
  expect(ctx.controller.detail.state.data).toBeNull()
  expect(ctx.controller.detail.state.error).toBe('')
})

test('permission removal immediately clears visible source read results', async () => {
  const ctx = await setup()
  vi.stubGlobal('fetch', async (url: string) =>
    Response.json(url.includes('?') ? { items: [source], next_cursor: 'cursor' } : source),
  )
  await ctx.controller.list.load()
  await ctx.controller.detail.load(sourceId)
  ctx.session.state.user!.permissions = ['source.manage']
  expect(ctx.controller.list.state.data).toBeNull()
  expect(ctx.controller.detail.state.data).toBeNull()
})

test('a confirmed registration cannot be duplicated by submitting unchanged inputs again', async () => {
  const ctx = await setup()
  const fetcher = vi.fn(async () => Response.json(source, { status: 201 }))
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.registration.submit()
  await ctx.controller.registration.submit()
  expect(fetcher).toHaveBeenCalledOnce()
})

test('source type arrays cannot pass the exact SourceCreate contract through string coercion', async () => {
  const ctx = await setup()
  Object.assign(ctx.draft, { source_type: ['synthetic'] })
  const fetcher = vi.fn(async () => Response.json(source, { status: 201 }))
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.registration.submit()
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.registration.state.error).not.toBe('')
})

test.each(['1', '12', '123', '1234', '12345', '123456', '1234560000'])(
  'RFC3339 expiry .%s preserves the original request precision and compares equivalent UTC instants',
  async (fraction) => {
    const ctx = await setup()
    ctx.draft.expires_at = `2026-11-21T08:00:00.${fraction}+08:00`
    const requests: RequestInit[] = []
    vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
      requests.push(init)
      return Response.json(
        {
          ...source,
          expires_at: `2026-11-21T00:00:00.${fraction.slice(0, 6)}Z`,
        },
        { status: 201 },
      )
    })
    await ctx.controller.registration.submit()
    expect(ctx.controller.registration.state.data).not.toBeNull()
    expect(JSON.parse(String(requests[0]?.body)).expires_at).toBe(ctx.draft.expires_at)
  },
)

test('contract-valid sub-microsecond precision is sent intact and authority refusal remains explicit', async () => {
  const ctx = await setup()
  ctx.draft.expires_at = '2026-11-21T08:00:00.1234567+08:00'
  const requests: RequestInit[] = []
  vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
    requests.push(init)
    return Response.json({ code: 'SOURCE_AUTHORIZATION_REQUIRED' }, { status: 403 })
  })
  await ctx.controller.registration.submit()
  expect(JSON.parse(String(requests[0]?.body)).expires_at).toBe(ctx.draft.expires_at)
  expect(ctx.controller.registration.state.error).toContain('SOURCE_AUTHORIZATION_REQUIRED')
  expect(ctx.controller.registration.state.uncertain).toBe(false)
})

test('nullable expiry is sent as null and does not fabricate an authorization deadline', async () => {
  const ctx = await setup()
  ctx.draft.expires_at = null
  vi.stubGlobal('fetch', async () =>
    Response.json({ ...source, expires_at: null }, { status: 201 }),
  )
  await ctx.controller.registration.submit()
  expect(ctx.controller.registration.state.data?.expires_at).toBeNull()
})

test.each(['2026-02-30T08:00:00Z', '2026-11-21T24:00:00Z', '2026-11-21T08:00:00', 'invalid'])(
  'invalid or missing-zone expiry %s is rejected before sending',
  async (expiry) => {
    const ctx = await setup()
    ctx.draft.expires_at = expiry
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.registration.submit()
    expect(fetcher).not.toHaveBeenCalled()
    expect(ctx.controller.registration.state.error).not.toBe('')
  },
)

test('editing a confirmed payload clears its result and creates a different key for the next intent', async () => {
  const ctx = await setup()
  const requests: RequestInit[] = []
  vi.stubGlobal('fetch', async (_url: string, init: RequestInit) => {
    requests.push(init)
    return Response.json({ ...source, name: ctx.draft.name }, { status: 201 })
  })
  await ctx.controller.registration.submit()
  ctx.draft.name = 'another self-owned source'
  expect(ctx.controller.registration.state.data).toBeNull()
  expect(ctx.controller.registration.state.message).toBe('')
  await ctx.controller.registration.submit()
  expect(requests).toHaveLength(2)
  expect(requests[1]?.headers).not.toEqual(requests[0]?.headers)
  expect(ctx.controller.registration.state.data?.name).toBe(ctx.draft.name)
})

test('manage permission revocation synchronously clears confirmed registration metadata', async () => {
  const ctx = await setup()
  vi.stubGlobal('fetch', async () => Response.json(source, { status: 201 }))
  await ctx.controller.registration.submit()
  ctx.session.state.user!.permissions = ['source.read']
  expect(ctx.controller.registration.state.data).toBeNull()
  expect(ctx.controller.registration.state.message).toBe('')
  expect(ctx.controller.registration.state.uncertain).toBe(false)
})

test('late failure after a case change cannot put an old error or retry intent into the new case', async () => {
  const ctx = await setup()
  let reject!: (reason: Error) => void
  const fetcher = vi.fn(() => new Promise<Response>((_resolve, fail) => (reject = fail)))
  vi.stubGlobal('fetch', fetcher)
  const pending = ctx.controller.registration.submit()
  ctx.selection.caseId = otherCase
  reject(new TypeError('self-owned network failure'))
  await pending
  expect(ctx.controller.registration.state.error).toBe('')
  expect(ctx.controller.registration.state.uncertain).toBe(false)
  await ctx.controller.registration.retry()
  expect(fetcher).toHaveBeenCalledOnce()
})

test.each([401, 403, 503])(
  'source list HTTP %i is explicit without showing cached rows',
  async (status) => {
    const ctx = await setup()
    vi.stubGlobal('fetch', async () => Response.json({ items: [source], next_cursor: null }))
    await ctx.controller.list.load()
    vi.stubGlobal('fetch', async () => Response.json({ code: 'SOURCE_READ_FAILURE' }, { status }))
    await ctx.controller.list.load()
    expect(ctx.controller.list.state.data).toBeNull()
    expect(ctx.controller.list.state.error).toContain('SOURCE_READ_FAILURE')
  },
)

test('read permission revocation during a request prevents a late page from becoming visible', async () => {
  const ctx = await setup()
  let release!: (response: Response) => void
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
  const pending = ctx.controller.list.load()
  ctx.session.state.user!.permissions = ['source.manage']
  release(Response.json({ items: [source], next_cursor: 'cursor' }))
  await pending
  expect(ctx.controller.list.state.data).toBeNull()
  expect(ctx.controller.list.state.error).toBe('')
  expect(ctx.controller.list.state.busy).toBe(false)
})

test('invalid pagination size cannot issue a source request', async () => {
  const ctx = await setup()
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.list.load(101)
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.list.state.error).not.toBe('')
})

const sourceEtag = '"self-owned-source-detail-etag-1"'
const anotherSourceId = '30000000-0000-4000-8000-000000000002'
const synchronized: Schemas['Source'] = {
  ...source,
  authorization_ref: 'self-owned-sync-authority/2',
  authorization_status: 'revoked',
  purpose: ['download'],
  expires_at: null,
  version: 2,
}

async function setupSync(permissions = ['source.read', 'source.manage']) {
  const ctx = await setup(permissions)
  expect(
    ctx.controller.authorizationSync,
    'the source synchronization controller is missing',
  ).toBeDefined()
  return ctx
}

async function readSyncDetail(
  ctx: Awaited<ReturnType<typeof setup>>,
  item = source,
  etag = sourceEtag,
) {
  vi.stubGlobal('fetch', async () => Response.json(item, { headers: { ETag: etag } }))
  await ctx.controller.detail.load(item.source_id)
}

test('detail retains only the actual strong service ETag and clears it with its binding', async () => {
  const ctx = await setup()
  await readSyncDetail(ctx)
  expect(ctx.controller.detail.state.etag).toBe(sourceEtag)
  expect(ctx.controller.detail.state.sourceId).toBe(sourceId)
  ctx.controller.detail.clear()
  expect(ctx.controller.detail.state.etag).toBeNull()
  expect(ctx.controller.detail.state.sourceId).toBe('')
})

test.each(['pending', 'verified', 'expired', 'revoked'] as const)(
  'sync sends only the read version and real ETag; authoritative %s is an acknowledgement, not approval',
  async (status) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    const requests: { url: string; init: RequestInit }[] = []
    const response = { ...synchronized, authorization_status: status }
    vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
      requests.push({ url, init })
      return Response.json(response, { headers: { ETag: '"sync-response-etag"' } })
    })
    await ctx.controller.authorizationSync.submit()
    expect(requests).toHaveLength(1)
    expect(requests[0]?.url).toBe(`/business/api/v1/sources/${sourceId}/authorization/sync`)
    expect(JSON.parse(String(requests[0]?.init.body))).toEqual({ expected_version: 1 })
    expect(requests[0]?.init.headers).toMatchObject({ 'If-Match': sourceEtag })
    const headers = requests[0]?.init.headers as Record<string, string>
    expect(headers['Idempotency-Key']).toMatch(/^[a-f0-9-]{36}$/)
    expect(ctx.controller.authorizationSync.state.data).toEqual(response)
    expect(ctx.controller.authorizationSync.state.message).toContain('不构成业务批准')
    expect(ctx.controller.detail.state.data).toBeNull()
    expect(ctx.controller.detail.state.etag).toBeNull()
    expect(ctx.controller.detail.state.sourceId).toBe(sourceId)
    await ctx.controller.authorizationSync.submit()
    expect(requests).toHaveLength(1)
  },
)

test('same authoritative version may produce a successful synchronization without incrementing the record', async () => {
  const ctx = await setupSync()
  await readSyncDetail(ctx)
  vi.stubGlobal('fetch', async () => Response.json(source))
  await ctx.controller.authorizationSync.submit()
  expect(ctx.controller.authorizationSync.state.data).toEqual(source)
})

test.each(['missing', 'weak', 'unquoted', 'oversized'])(
  'a %s ETag cannot authorize synchronization and is never replaced with a derived tag',
  async (kind) => {
    const ctx = await setupSync()
    const tags = {
      missing: null,
      weak: 'W/"weak"',
      unquoted: 'unquoted',
      oversized: `"${'x'.repeat(128)}"`,
    }
    const tag = tags[kind as keyof typeof tags]
    vi.stubGlobal('fetch', async () => Response.json(source, { headers: tag ? { ETag: tag } : {} }))
    await ctx.controller.detail.load(sourceId)
    expect(ctx.controller.detail.state.data).toEqual(source)
    expect(ctx.controller.detail.state.etag).toBeNull()
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.authorizationSync.submit()
    expect(fetcher).not.toHaveBeenCalled()
    expect(ctx.controller.authorizationSync.state.error).not.toBe('')
  },
)

test('source.manage cannot synchronize a source without a separately loaded detail', async () => {
  const ctx = await setupSync()
  vi.stubGlobal('fetch', async () => Response.json({ items: [source], next_cursor: null }))
  await ctx.controller.list.load()
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.authorizationSync.submit()
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.authorizationSync.state.error).not.toBe('')
})

test('source.read alone permits detail reading but cannot synchronize authorization', async () => {
  const ctx = await setupSync(['source.read'])
  await readSyncDetail(ctx)
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.authorizationSync.submit()
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.authorizationSync.state.error).toContain('PERMISSION_REQUIRED')
})

test.each([
  'source_id',
  'case_id',
  'name',
  'source_type',
  'version',
  'authorization_status',
  'purpose',
  'expires_at',
])(
  'sync rejects an invalid or unrelated response %s without losing its unknown intent',
  async (field) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    const invalid: Record<string, unknown> = {
      source_id: anotherSourceId,
      case_id: otherCase,
      name: 'unrelated source',
      source_type: 'public_licensed',
      version: 0,
      authorization_status: 'approved',
      purpose: [],
      expires_at: 'not-a-time',
    }
    vi.stubGlobal('fetch', async () => Response.json({ ...synchronized, [field]: invalid[field] }))
    await ctx.controller.authorizationSync.submit()
    expect(ctx.controller.authorizationSync.state.data).toBeNull()
    expect(ctx.controller.authorizationSync.state.error).not.toBe('')
    expect(ctx.controller.authorizationSync.state.message).toBe('')
    expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
  },
)

test.each([401, 403, 404, 409, 412, 422, 428, 503])(
  'first sync HTTP %i is explicit; another submission requires reloading its detail',
  async (status) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    const fetcher = vi.fn(async () => Response.json({ code: 'SOURCE_SYNC_REFUSED' }, { status }))
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.authorizationSync.submit()
    expect(ctx.controller.authorizationSync.state.data).toBeNull()
    expect(ctx.controller.authorizationSync.state.error).toContain('SOURCE_SYNC_REFUSED')
    expect(ctx.controller.authorizationSync.state.uncertain).toBe(status === 503)
    expect(ctx.controller.detail.state.etag).toBeNull()
    await ctx.controller.authorizationSync.submit()
    expect(fetcher).toHaveBeenCalledOnce()
  },
)

test.each(
  ['network', '503'].flatMap((first) => [409, 412, 403, 422].map((status) => ({ first, status }))),
)(
  'unknown sync $first then HTTP $status retains its original body/key/etag across new detail GETs',
  async ({ first, status }) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    const requests: RequestInit[] = []
    const fetcher = async (_url: string, init: RequestInit) => {
      requests.push(init)
      if (requests.length === 1) {
        if (first === 'network') throw new TypeError('self-owned unknown sync result')
        return Response.json({ code: 'SOURCE_SYNCHRONIZATION_UNAVAILABLE' }, { status: 503 })
      }
      if (requests.length === 2)
        return Response.json({ code: 'SOURCE_VERSION_CONFLICT' }, { status })
      return Response.json(synchronized)
    }
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.authorizationSync.submit()
    await ctx.controller.authorizationSync.retry()
    expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
    await readSyncDetail(ctx, { ...source, version: 7 }, '"new-current-detail-etag"')
    expect(ctx.controller.detail.state.etag).toBe('"new-current-detail-etag"')
    expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.authorizationSync.submit()
    expect(requests).toHaveLength(2)
    await ctx.controller.authorizationSync.retry()
    expect(requests).toHaveLength(3)
    for (const request of requests) {
      expect(request.body).toBe(requests[0]?.body)
      expect(request.headers).toEqual(requests[0]?.headers)
    }
    expect(JSON.parse(String(requests[2]?.body))).toEqual({ expected_version: 1 })
    expect(ctx.controller.authorizationSync.state.data).toEqual(synchronized)
    expect(ctx.controller.authorizationSync.state.uncertain).toBe(false)
    expect(ctx.controller.detail.state.data).toBeNull()
  },
)

test('first version conflict needs an explicit fresh read before a new intent can use its new version and ETag', async () => {
  const ctx = await setupSync()
  await readSyncDetail(ctx)
  const requests: RequestInit[] = []
  const fetcher = async (_url: string, init: RequestInit) => {
    requests.push(init)
    return requests.length === 1
      ? Response.json({ code: 'SOURCE_VERSION_CONFLICT' }, { status: 409 })
      : Response.json({ ...synchronized, version: 3 })
  }
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.authorizationSync.submit()
  await ctx.controller.authorizationSync.retry()
  await ctx.controller.authorizationSync.submit()
  expect(requests).toHaveLength(1)
  await readSyncDetail(ctx, { ...source, version: 2 }, '"fresh-version-2"')
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.authorizationSync.submit()
  expect(requests).toHaveLength(2)
  expect(JSON.parse(String(requests[1]?.body))).toEqual({ expected_version: 2 })
  expect(requests[1]?.headers).toMatchObject({ 'If-Match': '"fresh-version-2"' })
  expect(requests[1]?.headers).not.toEqual(requests[0]?.headers)
})

test.each(['case', 'identity', 'manage', 'read', 'source', 'dispose'])(
  'sync clears old sensitive results and discards late success after %s changes',
  async (change) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    let release!: (response: Response) => void
    const requests: string[] = []
    vi.stubGlobal('fetch', (url: string, init: RequestInit) => {
      requests.push(url)
      if (init.method === 'GET')
        return Promise.resolve(
          Response.json(
            { ...source, source_id: anotherSourceId },
            { headers: { ETag: '"another-source"' } },
          ),
        )
      return new Promise<Response>((resolve) => (release = resolve))
    })
    const pending = ctx.controller.authorizationSync.submit()
    await ctx.controller.authorizationSync.submit()
    expect(requests).toHaveLength(1)
    if (change === 'case') ctx.selection.caseId = otherCase
    if (change === 'identity') ctx.session.state.generation++
    if (change === 'manage') ctx.session.state.user!.permissions = ['source.read']
    if (change === 'read') ctx.session.state.user!.permissions = ['source.manage']
    if (change === 'source') await ctx.controller.detail.load(anotherSourceId)
    if (change === 'dispose') ctx.controller.dispose()
    release(Response.json(synchronized))
    await pending
    expect(ctx.controller.authorizationSync.state.data).toBeNull()
    expect(ctx.controller.authorizationSync.state.error).toBe('')
    expect(ctx.controller.authorizationSync.state.message).toBe('')
    expect(ctx.controller.authorizationSync.state.busy).toBe(false)
    await ctx.controller.authorizationSync.retry()
    expect(requests.filter((url) => url.endsWith('/authorization/sync'))).toHaveLength(1)
  },
)

test('registration and synchronization retain separate unknown intents and idempotency keys', async () => {
  const ctx = await setupSync()
  const requests: { url: string; init: RequestInit }[] = []
  const failures = new Set<string>()
  const fetcher = async (url: string, init: RequestInit) => {
    if (init.method === 'GET') return Response.json(source, { headers: { ETag: sourceEtag } })
    requests.push({ url, init })
    if (!failures.has(url)) {
      failures.add(url)
      throw new TypeError('self-owned unknown mutation result')
    }
    return Response.json(url.endsWith('/authorization/sync') ? synchronized : source)
  }
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.registration.submit()
  await ctx.controller.detail.load(sourceId)
  await ctx.controller.authorizationSync.submit()
  ctx.draft.name = 'edited registration only'
  expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
  ctx.draft.name = payload.name
  await ctx.controller.registration.retry()
  expect(ctx.controller.registration.state.data).toEqual(source)
  expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
  await ctx.controller.authorizationSync.retry()
  expect(ctx.controller.authorizationSync.state.data).toEqual(synchronized)
  expect(ctx.controller.registration.state.data).toEqual(source)
  const registrations = requests.filter((request) => request.url.endsWith('/sources'))
  const synchronizations = requests.filter((request) => request.url.endsWith('/authorization/sync'))
  expect(registrations).toHaveLength(2)
  expect(synchronizations).toHaveLength(2)
  expect(registrations[0]?.init.headers).toEqual(registrations[1]?.init.headers)
  expect(synchronizations[0]?.init.headers).toEqual(synchronizations[1]?.init.headers)
  expect(registrations[0]?.init.headers).not.toEqual(synchronizations[0]?.init.headers)
})

test.each(['source.read', 'source.manage'])(
  'revoking %s synchronously removes an already confirmed synchronization receipt',
  async (permission) => {
    const ctx = await setupSync()
    await readSyncDetail(ctx)
    vi.stubGlobal('fetch', async () => Response.json(synchronized))
    await ctx.controller.authorizationSync.submit()
    expect(ctx.controller.authorizationSync.state.data).toEqual(synchronized)
    ctx.session.state.user!.permissions = ctx.session.state.user!.permissions.filter(
      (value) => value !== permission,
    )
    expect(ctx.controller.authorizationSync.state.data).toBeNull()
    expect(ctx.controller.authorizationSync.state.message).toBe('')
  },
)

test('a positive but regressed sync version is rejected against its original detail', async () => {
  const ctx = await setupSync()
  await readSyncDetail(ctx, { ...source, version: 3 })
  vi.stubGlobal('fetch', async () => Response.json(synchronized))
  await ctx.controller.authorizationSync.submit()
  expect(ctx.controller.authorizationSync.state.data).toBeNull()
  expect(ctx.controller.authorizationSync.state.error).not.toBe('')
  expect(ctx.controller.authorizationSync.state.uncertain).toBe(true)
})

test('late synchronization failure cannot restore an old intent after switching the selected source', async () => {
  const ctx = await setupSync()
  await readSyncDetail(ctx)
  let reject!: (reason: Error) => void
  vi.stubGlobal('fetch', () => new Promise<Response>((_resolve, fail) => (reject = fail)))
  const pending = ctx.controller.authorizationSync.submit()
  await readSyncDetail(ctx, { ...source, source_id: anotherSourceId }, '"another-source-etag"')
  reject(new TypeError('self-owned late sync interruption'))
  await pending
  expect(ctx.controller.authorizationSync.state.error).toBe('')
  expect(ctx.controller.authorizationSync.state.uncertain).toBe(false)
  expect(ctx.controller.detail.state.etag).toBe('"another-source-etag"')
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.authorizationSync.retry()
  expect(fetcher).not.toHaveBeenCalled()
})

test('a late detail response cannot attach its old ETag to a different selected source', async () => {
  const ctx = await setupSync()
  let release!: (response: Response) => void
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => (release = resolve)))
  const pending = ctx.controller.detail.load(sourceId)
  const selected = { ...source, source_id: anotherSourceId }
  await readSyncDetail(ctx, selected, '"selected-source-etag"')
  release(Response.json(source, { headers: { ETag: sourceEtag } }))
  await pending
  expect(ctx.controller.detail.state.data).toEqual(selected)
  expect(ctx.controller.detail.state.etag).toBe('"selected-source-etag"')
  const requests: { url: string; init: RequestInit }[] = []
  vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
    requests.push({ url, init })
    return Response.json(selected)
  })
  await ctx.controller.authorizationSync.submit()
  expect(requests).toHaveLength(1)
  expect(requests[0]?.url).toBe(`/business/api/v1/sources/${anotherSourceId}/authorization/sync`)
  expect(requests[0]?.init.headers).toMatchObject({ 'If-Match': '"selected-source-etag"' })
  expect(ctx.controller.authorizationSync.state.data).toEqual(selected)
})
