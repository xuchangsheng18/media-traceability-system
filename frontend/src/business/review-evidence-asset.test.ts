import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import {
  createReviewEvidenceAsset,
  type ReviewEvidenceAssetSelection,
} from './review-evidence-asset'

const caseId = '20000000-0000-4000-8000-000000000001'
const taskId = '30000000-0000-4000-8000-000000000001'
const userId = '40000000-0000-4000-8000-000000000001'
const orgId = '50000000-0000-4000-8000-000000000001'
const evidenceId = '60000000-0000-4000-8000-000000000001'
const assetId = '70000000-0000-4000-8000-000000000001'
const objectId = '80000000-0000-4000-8000-000000000001'
const otherId = '90000000-0000-4000-8000-000000000001'
const bytes = new TextEncoder().encode('self-owned original evidence bytes')
async function sha(data: BufferSource) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('')
}
const active: ReturnType<typeof createReviewEvidenceAsset>[] = []
async function setup() {
  const digest = await sha(bytes)
  const evidence: Schemas['Evidence'] = {
    evidence_id: evidenceId,
    case_id: caseId,
    task_id: taskId,
    run_version: 3,
    result_version: 4,
    kind: 'original',
    asset_id: assetId,
    object_ref: { object_id: objectId, version_id: 'self-owned/fixed-1', sha256: digest },
    time_range: null,
    bbox: null,
    mapping_version: 'self-owned/mapping-1',
    model_name: null,
    model_version: null,
    authorization_version: 'self-owned/authorization-1',
    sha256: digest,
    version: 2,
    created_at: '2026-10-22T01:02:03.123456+08:00',
  }
  const value = reactive<ReviewEvidenceAssetSelection>({
    selection: {
      caseId,
      taskId,
      runVersion: 3,
      resultVersion: 4,
      sourceKey: 'context/self-owned-1',
      evidenceIds: null,
    },
    evidence,
    loaded: true,
    busy: false,
    page: { items: [evidence], next_cursor: null },
  })
  const asset: Schemas['Asset'] = {
    asset_id: assetId,
    case_id: caseId,
    content_id: assetId,
    source_id: assetId,
    kind: 'original',
    object_ref: { ...evidence.object_ref! },
    mime: 'application/octet-stream',
    size_bytes: bytes.length,
    duration_ms: null,
    width: null,
    height: null,
    state: 'VALID',
    version: 1,
    created_at: '2026-10-22T01:02:03Z',
  }
  const client = new BusinessClient()
  client.replaceToken('self-owned-original-evidence-token')
  const session = {
    state: reactive({
      generation: 1,
      user: {
        user_id: userId,
        org_id: orgId,
        roles: ['reviewer'],
        permissions: ['review.read', 'evidence.read', 'asset.read', 'asset.download'],
        case_ids: [caseId],
      } as Schemas['CurrentUser'] | null,
    }),
    call: client.call.bind(client),
    has: (permission: string) => session.state.user?.permissions.includes(permission) ?? false,
  }
  const save = vi.fn()
  const controller = createReviewEvidenceAsset(session, () => value, save)
  active.push(controller)
  const etag =
    '"' +
    (await sha(
      new TextEncoder().encode(JSON.stringify([objectId, asset.object_ref.version_id, digest])),
    )) +
    '"'
  return { value, asset, session, save, controller, etag }
}
afterEach(() => {
  active.splice(0).forEach((controller) => controller.dispose())
  vi.unstubAllGlobals()
})

test('explicit read binds the original evidence then reuses verified asset download', async () => {
  const ctx = await setup()
  const fetcher = vi.fn(async (url: string) =>
    url.endsWith('/content')
      ? new Response(bytes, { headers: { ETag: ctx.etag } })
      : Response.json(ctx.asset),
  )
  vi.stubGlobal('fetch', fetcher)
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.canLoad()).toBe(true)
  expect(ctx.controller.canDownload()).toBe(false)
  await ctx.controller.load()
  expect(fetcher.mock.calls.map((call) => call[0])).toEqual([`/business/api/v1/assets/${assetId}`])
  expect(ctx.controller.state.asset).toEqual(ctx.asset)
  expect(ctx.controller.canDownload()).toBe(true)
  await ctx.controller.download()
  expect(fetcher.mock.calls.map((call) => call[0])).toEqual([
    `/business/api/v1/assets/${assetId}`,
    `/business/api/v1/assets/${assetId}/content`,
  ])
  expect(ctx.save).toHaveBeenCalledExactlyOnceWith(expect.any(Blob), `asset-${assetId}.bin`)
  expect(ctx.controller.downloadState.message).toContain('已核验')
})

type Context = Awaited<ReturnType<typeof setup>>
function fields(value: unknown) {
  return value as Record<string, unknown>
}
function pending<T>() {
  let resolve!: (value: T) => void
  let reject!: (error: Error) => void
  const promise = new Promise<T>((pass, fail) => {
    resolve = pass
    reject = fail
  })
  return { promise, resolve, reject }
}
const invalidSelections: [string, (ctx: Context) => void][] = [
  [
    'no identity',
    (ctx) => {
      ctx.session.state.user = null
    },
  ],
  ...['review.read', 'evidence.read', 'asset.read'].map(
    (permission): [string, (ctx: Context) => void] => [
      `missing ${permission}`,
      (ctx) => {
        ctx.session.state.user!.permissions = ctx.session.state.user!.permissions.filter(
          (p) => p !== permission,
        )
      },
    ],
  ),
  [
    'case not visible',
    (ctx) => {
      ctx.session.state.user!.case_ids = [otherId]
    },
  ],
  [
    'no context',
    (ctx) => {
      ctx.value.selection = null
    },
  ],
  [
    'no selected evidence',
    (ctx) => {
      ctx.value.evidence = null
    },
  ],
  [
    'unloaded evidence page',
    (ctx) => {
      ctx.value.loaded = false
    },
  ],
  [
    'evidence reread pending',
    (ctx) => {
      ctx.value.busy = true
    },
  ],
  [
    'invalid actor id',
    (ctx) => {
      ctx.session.state.user!.user_id = 'bad'
    },
  ],
  [
    'invalid organization id',
    (ctx) => {
      ctx.session.state.user!.org_id = 'bad'
    },
  ],
  [
    'blank source key',
    (ctx) => {
      ctx.value.selection!.sourceKey = ' '
    },
  ],
  [
    'invalid context case',
    (ctx) => {
      ctx.value.selection!.caseId = 'bad'
    },
  ],
  [
    'other context case',
    (ctx) => {
      ctx.value.selection!.caseId = otherId
    },
  ],
  [
    'other context task',
    (ctx) => {
      ctx.value.selection!.taskId = otherId
    },
  ],
  [
    'other context run',
    (ctx) => {
      ctx.value.selection!.runVersion++
    },
  ],
  [
    'other context result',
    (ctx) => {
      ctx.value.selection!.resultVersion++
    },
  ],
  [
    'unsafe context run',
    (ctx) => {
      ctx.value.selection!.runVersion = Number.MAX_SAFE_INTEGER + 1
    },
  ],
  [
    'fractional context result',
    (ctx) => {
      ctx.value.selection!.resultVersion = 1.5
    },
  ],
  [
    'not associated with review',
    (ctx) => {
      ctx.value.selection!.evidenceIds = [otherId]
    },
  ],
  [
    'empty review references',
    (ctx) => {
      ctx.value.selection!.evidenceIds = []
    },
  ],
  [
    'invalid review reference',
    (ctx) => {
      ctx.value.selection!.evidenceIds = ['bad']
    },
  ],
  [
    'duplicate review references',
    (ctx) => {
      ctx.value.selection!.evidenceIds = [evidenceId, evidenceId.toUpperCase()]
    },
  ],
  ...['frame', 'region', 'segment', 'match', 'text', 'snapshot', 'model_output'].map(
    (kind): [string, (ctx: Context) => void] => [
      `nonoriginal ${kind}`,
      (ctx) => {
        fields(ctx.value.evidence).kind = kind
      },
    ],
  ),
  [
    'null evidence reference',
    (ctx) => {
      ctx.value.evidence!.object_ref = null
    },
  ],
  [
    'evidence checksum differs from object',
    (ctx) => {
      ctx.value.evidence!.sha256 = 'b'.repeat(64)
    },
  ],
  [
    'empty page',
    (ctx) => {
      ctx.value.page = { items: [], next_cursor: null }
    },
  ],
  [
    'null page',
    (ctx) => {
      ctx.value.page = null
    },
  ],
  [
    'wrong page cursor',
    (ctx) => {
      ctx.value.page = { items: [ctx.value.evidence], next_cursor: 2 }
    },
  ],
  [
    'unrecognized page field',
    (ctx) => {
      fields(ctx.value.page).untrusted = true
    },
  ],
  [
    'other page evidence',
    (ctx) => {
      ctx.value.page = {
        items: [{ ...ctx.value.evidence, evidence_id: otherId }],
        next_cursor: null,
      }
    },
  ],
]
test.each(invalidSelections)('%s refuses asset and content requests', async (_name, mutate) => {
  const ctx = await setup()
  mutate(ctx)
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  expect(ctx.controller.canLoad()).toBe(false)
  await ctx.controller.load()
  await ctx.controller.download()
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.controller.state.asset).toBeNull()
  expect(ctx.controller.state.loaded).toBe(false)
  expect(ctx.controller.canDownload()).toBe(false)
  expect(ctx.save).not.toHaveBeenCalled()
})

const evidenceDefects: [string, (value: Record<string, unknown>) => void][] = [
  [
    'extra evidence field',
    (v) => {
      v.untrusted = true
    },
  ],
  [
    'missing evidence field',
    (v) => {
      delete v.model_name
    },
  ],
  ...['evidence_id', 'case_id', 'task_id', 'asset_id'].map(
    (key): [string, (v: Record<string, unknown>) => void] => [
      `bad evidence ${key}`,
      (v) => {
        v[key] = 'bad'
      },
    ],
  ),
  [
    'zero evidence version',
    (v) => {
      v.version = 0
    },
  ],
  [
    'fractional evidence run',
    (v) => {
      v.run_version = 1.5
    },
  ],
  [
    'zero evidence result',
    (v) => {
      v.result_version = 0
    },
  ],
  [
    'bad evidence date',
    (v) => {
      v.created_at = '2026-02-30T00:00:00Z'
    },
  ],
  [
    'blank mapping',
    (v) => {
      v.mapping_version = ''
    },
  ],
  [
    'oversized authorization',
    (v) => {
      v.authorization_version = 'x'.repeat(129)
    },
  ],
  [
    'bad model name',
    (v) => {
      v.model_name = 2
    },
  ],
  [
    'bad model version',
    (v) => {
      v.model_version = ''
    },
  ],
  [
    'reference extra field',
    (v) => {
      fields(v.object_ref).untrusted = true
    },
  ],
  [
    'reference bad id',
    (v) => {
      fields(v.object_ref).object_id = 'bad'
    },
  ],
  [
    'reference empty version',
    (v) => {
      fields(v.object_ref).version_id = ''
    },
  ],
  [
    'reference uppercase hash',
    (v) => {
      fields(v.object_ref).sha256 = 'B'.repeat(64)
    },
  ],
  [
    'empty time range',
    (v) => {
      v.time_range = { start_ms: 0, end_ms: 0 }
    },
  ],
  [
    'negative time range',
    (v) => {
      v.time_range = { start_ms: -1, end_ms: 2 }
    },
  ],
  [
    'extra time range field',
    (v) => {
      v.time_range = { start_ms: 0, end_ms: 2, extra: 1 }
    },
  ],
  [
    'out of bounds region',
    (v) => {
      v.bbox = { x: 0.9, y: 0, width: 0.5, height: 0.5 }
    },
  ],
  [
    'empty region',
    (v) => {
      v.bbox = { x: 0, y: 0, width: 0, height: 1 }
    },
  ],
  [
    'bad region',
    (v) => {
      v.bbox = { x: 0, y: 0, width: 1 }
    },
  ],
]
test.each(evidenceDefects)(
  '%s is not blindly trusted from selected metadata',
  async (_name, mutate) => {
    const ctx = await setup()
    mutate(fields(ctx.value.evidence))
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    expect(ctx.controller.canLoad()).toBe(false)
    await ctx.controller.load()
    expect(fetcher).not.toHaveBeenCalled()
    expect(ctx.controller.state.asset).toBeNull()
  },
)

const assetDefects: [string, (value: Record<string, unknown>) => void][] = [
  ...[
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
  ].map((key): [string, (v: Record<string, unknown>) => void] => [
    `missing ${key}`,
    (v) => {
      delete v[key]
    },
  ]),
  [
    'extra field',
    (v) => {
      v.untrusted = true
    },
  ],
  ...['asset_id', 'case_id', 'content_id', 'source_id'].map(
    (key): [string, (v: Record<string, unknown>) => void] => [
      `bad ${key}`,
      (v) => {
        v[key] = 'bad'
      },
    ],
  ),
  [
    'wrong asset',
    (v) => {
      v.asset_id = otherId
    },
  ],
  [
    'wrong case',
    (v) => {
      v.case_id = otherId
    },
  ],
  [
    'derived kind',
    (v) => {
      v.kind = 'derived'
    },
  ],
  ...['VALIDATING', 'QUARANTINED', 'ARCHIVED', 'unrecognized'].map(
    (state): [string, (v: Record<string, unknown>) => void] => [
      `state ${state}`,
      (v) => {
        v.state = state
      },
    ],
  ),
  [
    'empty mime',
    (v) => {
      v.mime = ''
    },
  ],
  [
    'oversized mime',
    (v) => {
      v.mime = 'x'.repeat(129)
    },
  ],
  ...[0, -1, 0.5, Number.MAX_SAFE_INTEGER + 1, '1', null].map(
    (size): [string, (v: Record<string, unknown>) => void] => [
      `bad size ${size}`,
      (v) => {
        v.size_bytes = size
      },
    ],
  ),
  [
    'bad duration',
    (v) => {
      v.duration_ms = -1
    },
  ],
  [
    'fractional duration',
    (v) => {
      v.duration_ms = 1.5
    },
  ],
  [
    'bad width',
    (v) => {
      v.width = 0
    },
  ],
  [
    'bad height',
    (v) => {
      v.height = '1'
    },
  ],
  [
    'bad version',
    (v) => {
      v.version = 0
    },
  ],
  ...[
    '2026-02-30T00:00:00Z',
    '2026-10-22',
    '2026-10-22T24:00:00Z',
    '2026-10-22T00:60:00Z',
    '2026-10-22T00:00:00+24:00',
    '0000-01-01T00:00:00Z',
  ].map((date): [string, (v: Record<string, unknown>) => void] => [
    `bad date ${date}`,
    (v) => {
      v.created_at = date
    },
  ]),
  [
    'null reference',
    (v) => {
      v.object_ref = null
    },
  ],
  [
    'unregistered reference field',
    (v) => {
      fields(v.object_ref).url = 'https://example.invalid'
    },
  ],
  [
    'wrong object',
    (v) => {
      fields(v.object_ref).object_id = otherId
    },
  ],
  [
    'wrong fixed version',
    (v) => {
      fields(v.object_ref).version_id = 'self-owned/other'
    },
  ],
  [
    'empty fixed version',
    (v) => {
      fields(v.object_ref).version_id = ''
    },
  ],
  [
    'oversized fixed version',
    (v) => {
      fields(v.object_ref).version_id = 'x'.repeat(129)
    },
  ],
  [
    'wrong fixed hash',
    (v) => {
      fields(v.object_ref).sha256 = 'b'.repeat(64)
    },
  ],
  [
    'bad fixed hash',
    (v) => {
      fields(v.object_ref).sha256 = 'bad'
    },
  ],
]
test.each(assetDefects)('asset %s refuses a fallback or download', async (_name, mutate) => {
  const ctx = await setup()
  const broken = structuredClone(ctx.asset)
  mutate(fields(broken))
  const fetcher = vi.fn(async () => Response.json(broken))
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.load()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(ctx.controller.state.loaded).toBe(false)
  expect(ctx.controller.state.asset).toBeNull()
  expect(ctx.controller.state.error).toContain('不匹配')
  expect(ctx.controller.canDownload()).toBe(false)
  await ctx.controller.download()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(ctx.save).not.toHaveBeenCalled()
})

test('history references and canonical UUID equivalence keep an exact original eligible', async () => {
  const ctx = await setup()
  ctx.value.selection!.evidenceIds = [evidenceId.toUpperCase()]
  ctx.value.selection!.caseId = caseId.toUpperCase()
  ctx.asset.asset_id = assetId.toUpperCase()
  ctx.asset.case_id = caseId.toUpperCase()
  ctx.asset.object_ref.object_id = objectId.toUpperCase()
  ctx.asset.duration_ms = 0
  ctx.asset.width = 1
  ctx.asset.height = 1
  ctx.asset.created_at = '2024-02-29t23:59:59.123456z'
  vi.stubGlobal('fetch', async () => Response.json(ctx.asset))
  await ctx.controller.load()
  expect(ctx.controller.state.loaded).toBe(true)
  expect(ctx.controller.canDownload()).toBe(true)
})

test('asset detail permission and download permission stay independent', async () => {
  const ctx = await setup()
  ctx.session.state.user!.permissions = ['review.read', 'evidence.read', 'asset.read']
  const fetcher = vi.fn(async () => Response.json(ctx.asset))
  vi.stubGlobal('fetch', fetcher)
  expect(ctx.controller.canLoad()).toBe(true)
  await ctx.controller.load()
  expect(ctx.controller.state.loaded).toBe(true)
  expect(ctx.controller.canDownload()).toBe(false)
  await ctx.controller.download()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(ctx.save).not.toHaveBeenCalled()
})

test.each([401, 403, 404, 409, 422, 503])(
  'detail HTTP %i stays an error without content fallback',
  async (status) => {
    const ctx = await setup()
    const fetcher = vi.fn(async () => Response.json({ code: 'DEPENDENCY_UNAVAILABLE' }, { status }))
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.load()
    expect(ctx.controller.state.error).toContain('DEPENDENCY_UNAVAILABLE')
    expect(ctx.controller.state.loaded).toBe(false)
    expect(ctx.controller.state.asset).toBeNull()
    expect(ctx.controller.canDownload()).toBe(false)
    expect(fetcher).toHaveBeenCalledOnce()
  },
)

const changes: [string, (ctx: Context) => void][] = [
  [
    'generation',
    (ctx) => {
      ctx.session.state.generation++
    },
  ],
  [
    'same generation user',
    (ctx) => {
      ctx.session.state.user!.user_id = otherId
    },
  ],
  [
    'same generation organization',
    (ctx) => {
      ctx.session.state.user!.org_id = otherId
    },
  ],
  [
    'same generation roles',
    (ctx) => {
      ctx.session.state.user!.roles = ['analyst']
    },
  ],
  [
    'same generation permission',
    (ctx) => {
      ctx.session.state.user!.permissions = ['review.read']
    },
  ],
  [
    'same generation download permission',
    (ctx) => {
      ctx.session.state.user!.permissions = ['review.read', 'evidence.read', 'asset.read']
    },
  ],
  [
    'same generation visible cases',
    (ctx) => {
      ctx.session.state.user!.case_ids = []
    },
  ],
  [
    'disconnect',
    (ctx) => {
      ctx.session.state.user = null
    },
  ],
  [
    'selected evidence',
    (ctx) => {
      ctx.value.evidence = null
    },
  ],
  [
    'selected evidence version',
    (ctx) => {
      ctx.value.evidence!.version++
    },
  ],
  [
    'source context',
    (ctx) => {
      ctx.value.selection!.sourceKey = 'history/self-owned-2'
    },
  ],
  [
    'case',
    (ctx) => {
      ctx.value.selection!.caseId = otherId
    },
  ],
  [
    'task',
    (ctx) => {
      ctx.value.selection!.taskId = otherId
    },
  ],
  [
    'run',
    (ctx) => {
      ctx.value.selection!.runVersion++
    },
  ],
  [
    'result',
    (ctx) => {
      ctx.value.selection!.resultVersion++
    },
  ],
  [
    'evidence list',
    (ctx) => {
      ctx.value.selection!.evidenceIds = [evidenceId]
    },
  ],
  [
    'reader reread',
    (ctx) => {
      ctx.value.busy = true
    },
  ],
  [
    'reader clear',
    (ctx) => {
      ctx.value.loaded = false
    },
  ],
  [
    'next page',
    (ctx) => {
      ctx.value.page = { items: [], next_cursor: 'self-owned-next' }
    },
  ],
  [
    'clear',
    (ctx) => {
      ctx.controller.clear()
    },
  ],
  [
    'dispose',
    (ctx) => {
      ctx.controller.dispose()
    },
  ],
]
test.each(changes)(
  '%s immediately invalidates bound asset and download state',
  async (_name, change) => {
    const ctx = await setup()
    vi.stubGlobal('fetch', async () => Response.json(ctx.asset))
    await ctx.controller.load()
    expect(ctx.controller.state.loaded).toBe(true)
    ctx.controller.downloadState.message = 'self-owned previous message'
    change(ctx)
    expect(ctx.controller.state.asset).toBeNull()
    expect(ctx.controller.state.loaded).toBe(false)
    expect(ctx.controller.state.busy).toBe(false)
    expect(ctx.controller.state.error).toBe('')
    expect(ctx.controller.downloadState.message).toBe('')
    expect(ctx.controller.downloadState.error).toBe('')
    expect(ctx.controller.canDownload()).toBe(false)
  },
)

test.each(changes)(
  'late detail response after %s cannot restore or report failure',
  async (_name, change) => {
    const ctx = await setup()
    const delayed = pending<Response>()
    vi.stubGlobal('fetch', () => delayed.promise)
    const reading = ctx.controller.load()
    change(ctx)
    delayed.resolve(Response.json(ctx.asset))
    await reading
    expect(ctx.controller.state.asset).toBeNull()
    expect(ctx.controller.state.loaded).toBe(false)
    expect(ctx.controller.state.error).toBe('')
    expect(ctx.controller.state.busy).toBe(false)
  },
)

test.each(changes)(
  'late binary response after %s cannot save an old original',
  async (_name, change) => {
    const ctx = await setup()
    const delayed = pending<Response>()
    vi.stubGlobal('fetch', (url: string) =>
      url.endsWith('/content') ? delayed.promise : Promise.resolve(Response.json(ctx.asset)),
    )
    await ctx.controller.load()
    const downloading = ctx.controller.download()
    change(ctx)
    delayed.resolve(new Response(bytes, { headers: { ETag: ctx.etag } }))
    await downloading
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.downloadState.message).toBe('')
    expect(ctx.controller.downloadState.error).toBe('')
    expect(ctx.controller.downloadState.busy).toBe(false)
  },
)

test('duplicate read and download clicks issue only one pending request each', async () => {
  const ctx = await setup()
  const detail = pending<Response>()
  const binary = pending<Response>()
  const fetcher = vi.fn((url: string) =>
    url.endsWith('/content') ? binary.promise : detail.promise,
  )
  vi.stubGlobal('fetch', fetcher)
  const first = ctx.controller.load()
  await ctx.controller.load()
  expect(fetcher).toHaveBeenCalledOnce()
  detail.resolve(Response.json(ctx.asset))
  await first
  const second = ctx.controller.download()
  await ctx.controller.download()
  expect(fetcher).toHaveBeenCalledTimes(2)
  binary.resolve(new Response(bytes, { headers: { ETag: ctx.etag } }))
  await second
  expect(ctx.save).toHaveBeenCalledOnce()
})

test.each(['size', 'hash', 'etag', 'missing-etag'])(
  'binary %s mismatch never saves or reports success',
  async (defect) => {
    const ctx = await setup()
    vi.stubGlobal('fetch', async (url: string) =>
      url.endsWith('/content')
        ? new Response(
            defect === 'size'
              ? bytes.slice(1)
              : defect === 'hash'
                ? new Uint8Array(bytes.length)
                : bytes,
            {
              headers:
                defect === 'missing-etag' ? {} : { ETag: defect === 'etag' ? '"wrong"' : ctx.etag },
            },
          )
        : Response.json(ctx.asset),
    )
    await ctx.controller.load()
    await ctx.controller.download()
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.downloadState.error).toContain('核验')
    expect(ctx.controller.downloadState.message).toBe('')
  },
)

test('a late old detail error cannot overwrite a newly selected and verified original', async () => {
  const ctx = await setup()
  const old = pending<Response>()
  const fetcher = vi
    .fn()
    .mockImplementationOnce(() => old.promise)
    .mockImplementationOnce(async () => Response.json(ctx.asset))
  vi.stubGlobal('fetch', fetcher)
  const reading = ctx.controller.load()
  ctx.value.selection!.sourceKey = 'self-owned/replacement'
  await ctx.controller.load()
  old.reject(new Error('self-owned old network failure'))
  await reading
  expect(ctx.controller.state.asset).toEqual(ctx.asset)
  expect(ctx.controller.state.loaded).toBe(true)
  expect(ctx.controller.state.error).toBe('')
})

test('asset reread invalidates a pending binary response even with identical selection', async () => {
  const ctx = await setup()
  const binary = pending<Response>()
  vi.stubGlobal('fetch', (url: string) =>
    url.endsWith('/content') ? binary.promise : Promise.resolve(Response.json(ctx.asset)),
  )
  await ctx.controller.load()
  const downloading = ctx.controller.download()
  await ctx.controller.load()
  binary.resolve(new Response(bytes, { headers: { ETag: ctx.etag } }))
  await downloading
  expect(ctx.controller.state.loaded).toBe(true)
  expect(ctx.save).not.toHaveBeenCalled()
  expect(ctx.controller.downloadState.message).toBe('')
})

test('public bound asset state cannot be tampered into a different downloadable object', async () => {
  const ctx = await setup()
  const fetcher = vi.fn(async () => Response.json(ctx.asset))
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.load()
  ctx.controller.state.asset!.object_ref.version_id = 'self-owned/tampered'
  expect(ctx.controller.canDownload()).toBe(false)
  await ctx.controller.download()
  expect(fetcher).toHaveBeenCalledOnce()
  expect(ctx.save).not.toHaveBeenCalled()
})

test('selection changes while binary Blob bytes are pending prevents save after integrity work', async () => {
  const ctx = await setup()
  const data = pending<ArrayBuffer>()
  const started = pending<void>()
  const blob = new Blob([bytes])
  vi.spyOn(blob, 'arrayBuffer').mockImplementation(() => {
    started.resolve()
    return data.promise
  })
  const response = new Response(bytes, { headers: { ETag: ctx.etag } })
  vi.spyOn(response, 'blob').mockResolvedValue(blob)
  vi.stubGlobal('fetch', async (url: string) =>
    url.endsWith('/content') ? response : Response.json(ctx.asset),
  )
  await ctx.controller.load()
  const downloading = ctx.controller.download()
  await started.promise
  ctx.value.selection!.sourceKey = 'self-owned/new-source'
  data.resolve(bytes.buffer)
  await downloading
  expect(ctx.save).not.toHaveBeenCalled()
  expect(ctx.controller.downloadState.message).toBe('')
  expect(ctx.controller.downloadState.error).toBe('')
})

test.each(['source', 'identity', 'reader', 'dispose'])(
  'late binary error after %s is discarded',
  async (change) => {
    const ctx = await setup()
    const binary = pending<Response>()
    vi.stubGlobal('fetch', (url: string) =>
      url.endsWith('/content') ? binary.promise : Promise.resolve(Response.json(ctx.asset)),
    )
    await ctx.controller.load()
    const downloading = ctx.controller.download()
    if (change === 'source') ctx.value.selection!.sourceKey = 'self-owned/new-source'
    if (change === 'identity') ctx.session.state.user!.user_id = otherId
    if (change === 'reader') ctx.value.busy = true
    if (change === 'dispose') ctx.controller.dispose()
    binary.reject(new Error('self-owned old binary failure'))
    await downloading
    expect(ctx.save).not.toHaveBeenCalled()
    expect(ctx.controller.downloadState.error).toBe('')
    expect(ctx.controller.downloadState.message).toBe('')
    expect(ctx.controller.downloadState.busy).toBe(false)
  },
)

test('valid evidence alone cannot download without an explicit verified asset read', async () => {
  const ctx = await setup()
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  await ctx.controller.download()
  expect(fetcher).not.toHaveBeenCalled()
  expect(ctx.save).not.toHaveBeenCalled()
  expect(ctx.controller.downloadState.message).toBe('')
})

test.each([null, [], 1, 'self-owned invalid response'])(
  'invalid top-level asset response %j stays unavailable',
  async (body) => {
    const ctx = await setup()
    const fetcher = vi.fn(async () => Response.json(body))
    vi.stubGlobal('fetch', fetcher)
    await ctx.controller.load()
    expect(ctx.controller.state.asset).toBeNull()
    expect(ctx.controller.state.loaded).toBe(false)
    expect(ctx.controller.canDownload()).toBe(false)
    expect(fetcher).toHaveBeenCalledOnce()
  },
)
