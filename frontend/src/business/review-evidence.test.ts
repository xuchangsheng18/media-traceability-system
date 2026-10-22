import { afterEach, expect, test, vi } from 'vitest'
import { reactive, shallowRef } from 'vue'
import { BusinessClient, type Schemas } from './api'
import { createReviewEvidenceReader, type ReviewEvidenceSelection } from './review-evidence'
import type { BusinessSession } from './session'

const caseId = '20000000-0000-4000-8000-000000000001'
const taskId = '30000000-0000-4000-8000-000000000001'
const userId = '40000000-0000-4000-8000-000000000001'
const orgId = '50000000-0000-4000-8000-000000000001'
const evidenceId = '6a000000-0000-4000-8000-000000000001'
const otherId = '60000000-0000-4000-8000-000000000002'
function evidence(): Schemas['Evidence'] {
  return {
    evidence_id: evidenceId,
    case_id: caseId,
    task_id: taskId,
    run_version: 3,
    result_version: 4,
    kind: 'region',
    asset_id: otherId,
    object_ref: { object_id: otherId, version_id: 'self-owned/object-1', sha256: 'b'.repeat(64) },
    time_range: { start_ms: 10, end_ms: 20 },
    bbox: { x: 0.1, y: 0.2, width: 0.3, height: 0.4 },
    mapping_version: 'self-owned/mapping-1',
    model_name: null,
    model_version: null,
    authorization_version: 'self-owned/authorization-1',
    sha256: 'a'.repeat(64),
    version: 2,
    created_at: '2026-10-22T01:02:03.123456+08:00',
  }
}
function selection(): ReviewEvidenceSelection {
  return {
    caseId,
    taskId,
    runVersion: 3,
    resultVersion: 4,
    sourceKey: 'context/self-owned-1',
    evidenceIds: null,
  }
}
function response(
  data: unknown = { items: [evidence()], next_cursor: null },
  headers: Record<string, string> = {},
) {
  return Response.json(data, {
    headers: { 'X-Task-Id': taskId, 'X-Run-Version': '3', 'X-Result-Version': '4', ...headers },
  })
}
const active: ReturnType<typeof createReviewEvidenceReader>[] = []
function setup() {
  const client = new BusinessClient()
  client.replaceToken('self-owned-evidence-reader-token')
  const session = {
    state: reactive({
      generation: 1,
      user: {
        user_id: userId,
        org_id: orgId,
        roles: ['reviewer'],
        permissions: ['review.read', 'evidence.read'],
        case_ids: [caseId],
      } as Schemas['CurrentUser'] | null,
    }),
    call: client.call.bind(client),
    has: (permission: string): boolean =>
      session.state.user?.permissions.includes(permission) ?? false,
  } satisfies Pick<BusinessSession, 'call' | 'has'> & {
    state: Pick<BusinessSession['state'], 'generation' | 'user'>
  }
  const value = shallowRef<ReviewEvidenceSelection | null>(selection())
  const reader = createReviewEvidenceReader(session, () => value.value)
  active.push(reader)
  return { session, value, reader }
}
afterEach(() => {
  active.splice(0).forEach((reader) => reader.dispose())
  vi.unstubAllGlobals()
})

test('reads only the exact historical GET and locally locates identifiers without fetching objects', async () => {
  const fetch = vi.fn(async (_url: string, _init: RequestInit) => response())
  vi.stubGlobal('fetch', fetch)
  const { reader } = setup()
  expect(reader.canLoad()).toBe(true)
  await reader.load()
  const [url, init] = fetch.mock.calls[0]!
  expect(url).toBe(
    `/business/api/v1/analysis/tasks/${taskId}/evidence?history%5Brun_version%5D=3&history%5Bresult_version%5D=4`,
  )
  expect(init.method).toBe('GET')
  expect(init.body).toBeUndefined()
  expect(init.headers).toMatchObject({ Authorization: 'Bearer self-owned-evidence-reader-token' })
  expect(reader.state.loaded).toBe(true)
  expect(reader.visibleItems()).toEqual([evidence()])
  expect(reader.selected()).toBeNull()
  reader.locate(evidenceId.toUpperCase())
  expect(reader.selected()).toEqual(evidence())
  expect(reader.state.selectedId).toBe(evidenceId)
  reader.locate(otherId)
  expect(reader.selected()).toBeNull()
  expect(fetch).toHaveBeenCalledTimes(1)
})
test('historical references expose missing identifiers and partial-page cursor without fetching another page', async () => {
  const fetch = vi.fn(async () =>
    response({
      items: [evidence(), { ...evidence(), evidence_id: userId }],
      next_cursor: 'opaque+cursor/=?',
    }),
  )
  vi.stubGlobal('fetch', fetch)
  const { reader, value } = setup()
  value.value = {
    ...selection(),
    sourceKey: 'review/self-owned-2',
    evidenceIds: [evidenceId.toUpperCase(), otherId],
  }
  await reader.load()
  expect(reader.visibleItems()).toEqual([evidence()])
  expect(reader.missingIds()).toEqual([otherId])
  expect(reader.state.data?.next_cursor).toBe('opaque+cursor/=?')
  reader.locate(userId)
  expect(reader.selected()).toBeNull()
  reader.locate(otherId)
  expect(reader.selected()).toBeNull()
  expect(reader.state.loaded).toBe(true)
  expect(fetch).toHaveBeenCalledTimes(1)
})
test('an empty historical page reports linked IDs missing rather than successful location', async () => {
  vi.stubGlobal('fetch', async () => response({ items: [], next_cursor: null }))
  const { reader, value } = setup()
  value.value = { ...selection(), sourceKey: 'review/self-owned-1', evidenceIds: [evidenceId] }
  await reader.load()
  expect(reader.state.loaded).toBe(true)
  expect(reader.state.error).toBe('')
  expect(reader.visibleItems()).toEqual([])
  expect(reader.missingIds()).toEqual([evidenceId])
  reader.locate(evidenceId)
  expect(reader.selected()).toBeNull()
})
test('empty current pages are valid and nullable locators remain explicit', async () => {
  vi.stubGlobal('fetch', async () => response({ items: [], next_cursor: null }))
  const { reader } = setup()
  await reader.load()
  expect(reader.state.loaded).toBe(true)
  expect(reader.state.error).toBe('')
  expect(reader.missingIds()).toEqual([])
})
test('accepts all nullable locator/model fields and finite boundary geometry', async () => {
  vi.stubGlobal('fetch', async () =>
    response({
      items: [
        {
          ...evidence(),
          object_ref: null,
          time_range: null,
          bbox: { x: 0, y: 0, width: 1, height: 1 },
          model_name: 'self-owned',
          model_version: '1',
        },
      ],
      next_cursor: null,
    }),
  )
  const { reader } = setup()
  await reader.load()
  expect(reader.state.loaded).toBe(true)
})

test.each(['original', 'frame', 'region', 'segment', 'match', 'text', 'snapshot', 'model_output'])(
  'accepts schema kind %s without inventing kind-specific locator requirements',
  async (kind) => {
    vi.stubGlobal('fetch', async () =>
      response({
        items: [{ ...evidence(), kind, object_ref: null, time_range: null, bbox: null }],
        next_cursor: null,
      }),
    )
    const { reader } = setup()
    await reader.load()
    expect(reader.state.loaded).toBe(true)
    expect(reader.visibleItems()[0]?.kind).toBe(kind)
  },
)

test.each(['no-user', 'no-review', 'no-evidence', 'hidden-case'])(
  'makes zero requests for %s',
  async (mode) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const { reader, session } = setup()
    if (mode === 'no-user') session.state.user = null
    if (mode === 'no-review') session.state.user!.permissions = ['evidence.read']
    if (mode === 'no-evidence') session.state.user!.permissions = ['review.read']
    if (mode === 'hidden-case') session.state.user!.case_ids = []
    expect(reader.canLoad()).toBe(false)
    await reader.load()
    expect(reader.state.loaded).toBe(false)
    expect(reader.state.error).not.toBe('')
    expect(fetch).not.toHaveBeenCalled()
  },
)
test.each([
  null,
  { caseId: '../case' },
  { taskId: '../task' },
  { runVersion: 0 },
  { resultVersion: 1.2 },
  { runVersion: Number.MAX_SAFE_INTEGER + 1 },
  { resultVersion: Number.NaN },
  { sourceKey: '' },
  { sourceKey: ' ' },
  { evidenceIds: [] },
  { evidenceIds: ['invalid'] },
  { evidenceIds: [evidenceId, evidenceId.toUpperCase()] },
])('makes zero requests for malformed selection %j', async (change) => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  const { reader, value } = setup()
  value.value = change === null ? null : { ...selection(), ...change }
  expect(reader.canLoad()).toBe(false)
  await reader.load()
  expect(reader.state.data).toBeNull()
  expect(reader.state.error).not.toBe('')
  expect(fetch).not.toHaveBeenCalled()
})
test.each([403, 404, 503])(
  'preserves HTTP %s as an error rather than an empty page',
  async (status) => {
    vi.stubGlobal('fetch', async () => Response.json({ code: 'SELF_OWNED_FAILURE' }, { status }))
    const { reader } = setup()
    await reader.load()
    expect(reader.state.data).toBeNull()
    expect(reader.state.loaded).toBe(false)
    expect(reader.state.error).toContain('SELF_OWNED_FAILURE')
  },
)
test.each(['X-Task-Id', 'X-Run-Version', 'X-Result-Version'])(
  'requires %s even for an empty page',
  async (header) => {
    const body = response({ items: [], next_cursor: null })
    body.headers.delete(header)
    vi.stubGlobal('fetch', async () => body)
    const { reader } = setup()
    await reader.load()
    expect(reader.state.loaded).toBe(false)
    expect(reader.state.error).toContain('已拒绝显示')
  },
)
test.each([
  { 'X-Task-Id': otherId },
  { 'X-Task-Id': 'invalid' },
  { 'X-Run-Version': '2' },
  { 'X-Run-Version': '03' },
  { 'X-Result-Version': '5' },
  { 'X-Result-Version': '4.0' },
] as Record<string, string>[])('rejects mismatched response binding %j', async (headers) => {
  vi.stubGlobal('fetch', async () => response({ items: [], next_cursor: null }, headers))
  const { reader } = setup()
  await reader.load()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.error).toContain('已拒绝显示')
})
test.each(Object.keys(evidence()))('requires Evidence.%s', async (field) => {
  const item: Record<string, unknown> = evidence()
  delete item[field]
  vi.stubGlobal('fetch', async () => response({ items: [item], next_cursor: null }))
  const { reader } = setup()
  await reader.load()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.data).toBeNull()
})
test.each([
  { evidence_id: 'invalid' },
  { case_id: otherId },
  { task_id: otherId },
  { run_version: 2 },
  { result_version: 5 },
  { run_version: 1.5 },
  { result_version: 0 },
  { kind: 'download' },
  { asset_id: null },
  { mapping_version: '' },
  { mapping_version: 'x'.repeat(129) },
  { authorization_version: '' },
  { authorization_version: 'x'.repeat(129) },
  { model_name: '' },
  { model_name: 'x'.repeat(129) },
  { model_version: '' },
  { model_version: 1 },
  { sha256: 'A'.repeat(64) },
  { sha256: 'a'.repeat(63) },
  { version: 0 },
  { version: 1.2 },
  { version: Number.MAX_SAFE_INTEGER + 1 },
  { created_at: '2026-10-22' },
  { created_at: '2026-02-30T01:02:03Z' },
  { created_at: '2026-10-22T24:00:00Z' },
  { created_at: '2026-10-22T01:02:03+24:00' },
  { unexpected: true },
  {
    object_ref: {
      object_id: otherId,
      version_id: '1',
      sha256: 'a'.repeat(64),
      url: 'https://invalid.example',
    },
  },
  { object_ref: { object_id: 'invalid', version_id: '1', sha256: 'a'.repeat(64) } },
  { object_ref: { object_id: otherId, version_id: '', sha256: 'a'.repeat(64) } },
  { object_ref: { object_id: otherId, version_id: 'a'.repeat(129), sha256: 'a'.repeat(64) } },
  { object_ref: { object_id: otherId, version_id: '1', sha256: 'A'.repeat(64) } },
  { time_range: { start_ms: -1, end_ms: 20 } },
  { time_range: { start_ms: 10, end_ms: 10 } },
  { time_range: { start_ms: 20, end_ms: 10 } },
  { time_range: { start_ms: 1.2, end_ms: 20 } },
  { time_range: { start_ms: 0, end_ms: Number.MAX_SAFE_INTEGER + 1 } },
  { time_range: { start_ms: 0, end_ms: 20, extra: true } },
  { bbox: { x: -0.1, y: 0, width: 0.2, height: 0.3 } },
  { bbox: { x: 0, y: 0, width: 0, height: 0.3 } },
  { bbox: { x: 0.8, y: 0, width: 0.3, height: 0.3 } },
  { bbox: { x: 0, y: 0.8, width: 0.3, height: 0.3 } },
  { bbox: { x: 0, y: 0, width: 0.3, height: 0.3, extra: true } },
])('rejects malformed nested schema or wrong task/case/version %j', async (change) => {
  vi.stubGlobal('fetch', async () =>
    response({ items: [{ ...evidence(), ...change }], next_cursor: null }),
  )
  const { reader } = setup()
  await reader.load()
  expect(reader.state.data).toBeNull()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.error).toContain('已拒绝显示')
})
test.each([
  null,
  [],
  {},
  { items: [] },
  { items: null, next_cursor: null },
  { items: [], next_cursor: '' },
  { items: [], next_cursor: 'x'.repeat(129) },
  { items: [], next_cursor: null, extra: true },
  { items: [evidence(), evidence()], next_cursor: null },
  {
    items: [evidence(), { ...evidence(), evidence_id: evidenceId.toUpperCase() }],
    next_cursor: null,
  },
])('rejects malformed or ambiguous evidence pages %j', async (data) => {
  vi.stubGlobal('fetch', async () => response(data))
  const { reader } = setup()
  await reader.load()
  expect(reader.state.data).toBeNull()
  expect(reader.state.loaded).toBe(false)
})
for (const field of ['object_ref', 'time_range', 'bbox'] as const) {
  test.each(Object.keys(evidence()[field]!))(`requires ${field}.%s`, async (key) => {
    const item = evidence()
    const nested: Record<string, unknown> = { ...item[field] }
    delete nested[key]
    vi.stubGlobal('fetch', async () =>
      response({ items: [{ ...item, [field]: nested }], next_cursor: null }),
    )
    const { reader } = setup()
    await reader.load()
    expect(reader.state.loaded).toBe(false)
  })
}

type Environment = ReturnType<typeof setup>
const changes: [string, (env: Environment) => void][] = [
  [
    'review permission revoked',
    ({ session }) => {
      session.state.user!.permissions = ['evidence.read']
    },
  ],
  [
    'evidence permission revoked',
    ({ session }) => {
      session.state.user!.permissions = ['review.read']
    },
  ],
  [
    'membership removed',
    ({ session }) => {
      session.state.user!.case_ids = []
    },
  ],
  [
    'generation',
    ({ session }) => {
      session.state.generation++
    },
  ],
  [
    'logout',
    ({ session }) => {
      session.state.user = null
    },
  ],
  [
    'user',
    ({ session }) => {
      session.state.user!.user_id = otherId
    },
  ],
  [
    'org',
    ({ session }) => {
      session.state.user!.org_id = otherId
    },
  ],
  [
    'roles',
    ({ session }) => {
      session.state.user!.roles.push('analyst')
    },
  ],
  [
    'permissions',
    ({ session }) => {
      session.state.user!.permissions.push('other.read')
    },
  ],
  [
    'membership',
    ({ session }) => {
      session.state.user!.case_ids.push(otherId)
    },
  ],
  [
    'case',
    ({ value }) => {
      value.value = { ...selection(), caseId: otherId }
    },
  ],
  [
    'task',
    ({ value }) => {
      value.value = { ...selection(), taskId: otherId }
    },
  ],
  [
    'run',
    ({ value }) => {
      value.value = { ...selection(), runVersion: 5 }
    },
  ],
  [
    'result',
    ({ value }) => {
      value.value = { ...selection(), resultVersion: 6 }
    },
  ],
  [
    'source with unchanged result versions',
    ({ value }) => {
      value.value = { ...selection(), sourceKey: 'review/another-source' }
    },
  ],
  [
    'evidence references',
    ({ value }) => {
      value.value = { ...selection(), evidenceIds: [otherId] }
    },
  ],
  [
    'no-selection',
    ({ value }) => {
      value.value = null
    },
  ],
  [
    'dispose',
    ({ reader }) => {
      reader.dispose()
    },
  ],
]
test.each(changes)(
  '%s synchronously clears loaded data and selected evidence',
  async (_name, change) => {
    vi.stubGlobal('fetch', async () => response())
    const env = setup()
    await env.reader.load()
    env.reader.locate(evidenceId)
    expect(env.reader.selected()).not.toBeNull()
    change(env)
    expect(env.reader.state.data).toBeNull()
    expect(env.reader.state.selectedId).toBe('')
    expect(env.reader.state.loaded).toBe(false)
    expect(env.reader.state.busy).toBe(false)
  },
)
test.each(
  changes.flatMap(([name, change]) => [
    [name, change, false] as const,
    [name, change, true] as const,
  ]),
)('%s discards late native Promise completion (error=%s)', async (_name, change, error) => {
  let finish!: (response: Response) => void
  const fetch = vi.fn(
    () =>
      new Promise<Response>((resolve) => {
        finish = resolve
      }),
  )
  vi.stubGlobal('fetch', fetch)
  const env = setup()
  const pending = env.reader.load()
  expect(env.reader.state.busy).toBe(true)
  change(env)
  finish(error ? Response.json({ code: 'SELF_OWNED_LATE' }, { status: 503 }) : response())
  await pending
  expect(env.reader.state).toEqual({
    data: null,
    busy: false,
    error: '',
    loaded: false,
    selectedId: '',
  })
  expect(fetch).toHaveBeenCalledTimes(1)
})
test('manual clear invalidates pending reads and dispose prevents any further request', async () => {
  let finish!: (response: Response) => void
  const fetch = vi.fn(
    () =>
      new Promise<Response>((resolve) => {
        finish = resolve
      }),
  )
  vi.stubGlobal('fetch', fetch)
  const { reader } = setup()
  const pending = reader.load()
  reader.clear()
  finish(response())
  await pending
  expect(reader.state.data).toBeNull()
  reader.dispose()
  await reader.load()
  expect(reader.canLoad()).toBe(false)
  expect(fetch).toHaveBeenCalledTimes(1)
})

test.each([false, true])(
  'a superseded load cannot clear or overwrite the new pending read (error=%s)',
  async (error) => {
    const finish: ((response: Response) => void)[] = []
    vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => finish.push(resolve)))
    const { reader } = setup()
    const first = reader.load()
    const second = reader.load()
    finish[0]!(
      error ? Response.json({ code: 'SELF_OWNED_SUPERSEDED' }, { status: 503 }) : response(),
    )
    await first
    expect(reader.state).toEqual({
      data: null,
      busy: true,
      error: '',
      loaded: false,
      selectedId: '',
    })
    finish[1]!(response({ items: [], next_cursor: null }))
    await second
    expect(reader.state.data).toEqual({ items: [], next_cursor: null })
    expect(reader.state.loaded).toBe(true)
    expect(reader.state.busy).toBe(false)
    expect(reader.state.error).toBe('')
  },
)

test('reactive in-place historical reference changes clear a loaded selection immediately', async () => {
  vi.stubGlobal('fetch', async () => response())
  const { reader, value } = setup()
  const selected = reactive({ ...selection(), evidenceIds: [evidenceId] })
  value.value = selected
  await reader.load()
  reader.locate(evidenceId)
  expect(reader.selected()).not.toBeNull()
  selected.evidenceIds.push(otherId)
  expect(reader.state.data).toBeNull()
  expect(reader.state.selectedId).toBe('')
  expect(reader.state.loaded).toBe(false)
})
