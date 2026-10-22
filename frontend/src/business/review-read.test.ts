import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import { createTaskReviewReader } from './review-read'
import type { BusinessSession } from './session'

const caseId = '20000000-0000-4000-8000-000000000001'
const otherCaseId = '20000000-0000-4000-8000-000000000002'
const taskId = '30000000-0000-4000-8000-000000000001'
const otherTaskId = '30000000-0000-4000-8000-000000000002'
const userId = '40000000-0000-4000-8000-000000000001'
const orgId = '50000000-0000-4000-8000-000000000001'
const evidenceId = '60000000-0000-4000-8000-000000000001'
function context(id = taskId): Schemas['ReviewContext'] {
  return {
    task_id: id,
    run_version: 3,
    result_version: 4,
    policy_version: 'self-owned-policy/2',
    snapshot_sha256: 'a'.repeat(64),
    object_version: 5,
    review_version: 0,
  }
}
function review(id = taskId): Schemas['Review'] {
  return {
    review_id: otherTaskId,
    reviewer_id: userId,
    task_id: id,
    run_version: 1,
    result_version: 2,
    expected_review_version: 0,
    decision: 'return_for_evidence',
    reason: 'Self-owned evidence needs another observation.',
    evidence_ids: [evidenceId],
    policy_version: 'self-owned-history-policy/1',
    review_version: 1,
    created_at: '2026-10-22T01:02:03.123456+08:00',
  }
}
function page(id = taskId): Schemas['ReviewPage'] {
  return { items: [review(id)], next_cursor: 'opaque+cursor/with?=&%' }
}
const active: ReturnType<typeof createTaskReviewReader>[] = []
function setup() {
  const client = new BusinessClient()
  client.replaceToken('self-owned-review-read-token')
  const session = {
    state: reactive({
      generation: 1,
      user: {
        user_id: userId,
        org_id: orgId,
        roles: ['reviewer'],
        permissions: ['review.read'],
        case_ids: [caseId, otherCaseId],
      } as Schemas['CurrentUser'] | null,
    }),
    call: client.call.bind(client),
    has: (permission: string): boolean =>
      session.state.user?.permissions.includes(permission) ?? false,
  } satisfies Pick<BusinessSession, 'call' | 'has'> & {
    state: Pick<BusinessSession['state'], 'generation' | 'user'>
  }
  const reader = createTaskReviewReader(session)
  active.push(reader)
  return { session, reader }
}
afterEach(() => {
  active.splice(0).forEach((reader) => reader.dispose())
  vi.unstubAllGlobals()
})

test.each([null, '"server-exact-opaque"', 'W/"read-only-weak"'])(
  'context remains readable with %s header and preserves server bytes without guessing a tag',
  async (etag) => {
    vi.stubGlobal('fetch', async () =>
      Response.json(context(), { headers: etag ? { ETag: etag } : {} }),
    )
    const { reader } = setup()
    await reader.loadContext(caseId, taskId)
    expect(reader.state.context.data).toEqual(context())
    expect(reader.state.context.etag).toBe(etag)
    reader.clear()
    expect(reader.state.context.etag).toBeNull()
  },
)

test('context reread immediately clears the previous condition before the replacement arrives', async () => {
  let finish!: (response: Response) => void
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(Response.json(context(), { headers: { ETag: '"first-context"' } }))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((done) => {
            finish = done
          }),
      ),
  )
  const { reader } = setup()
  await reader.loadContext(caseId, taskId)
  const replacement = reader.loadContext(caseId, taskId)
  expect(reader.state.context.data).toBeNull()
  expect(reader.state.context.etag).toBeNull()
  finish(Response.json({ code: 'TEST_ONLY_NO_RESULT' }, { status: 404 }))
  await replacement
  expect(reader.state.context.data).toBeNull()
  expect(reader.state.context.etag).toBeNull()
})

test('reads exact existing GET endpoints and keeps historical result versions separate', async () => {
  const requests: { url: string; init: RequestInit }[] = []
  vi.stubGlobal('fetch', async (url: string, init: RequestInit) => {
    requests.push({ url, init })
    return Response.json(url.includes('review-context') ? context() : page())
  })
  const { reader } = setup()
  await Promise.all([
    reader.loadContext(caseId.toUpperCase(), taskId.toUpperCase()),
    reader.loadHistory(caseId, taskId),
  ])
  expect(requests.map((request) => request.url)).toEqual([
    `/business/api/v1/analysis/tasks/${taskId}/review-context`,
    `/business/api/v1/reviews?case_id=${caseId}&limit=20&task_id=${taskId}`,
  ])
  expect(requests.every((request) => request.init.method === 'GET')).toBe(true)
  expect(requests.every((request) => request.init.body === undefined)).toBe(true)
  expect(reader.state.context.data).toEqual(context())
  expect(reader.state.history.data).toEqual(page())
  expect(reader.state.context.loaded).toBe(true)
  expect(reader.state.history.loaded).toBe(true)
  expect(reader.state.history.data?.items[0]?.run_version).toBe(1)
  expect(reader.state.context.data?.run_version).toBe(3)
})

test('encodes the supplied opaque cursor once while preserving task and case scope', async () => {
  const fetch = vi.fn(async (_url: string) => Response.json({ items: [], next_cursor: null }))
  vi.stubGlobal('fetch', fetch)
  const { reader } = setup()
  const cursor = 'opaque+cursor/with?=&%'
  await reader.loadHistory(caseId, taskId, cursor)
  const url = new URL(fetch.mock.calls[0]![0], 'http://localhost')
  expect(url.searchParams.get('case_id')).toBe(caseId)
  expect(url.searchParams.get('task_id')).toBe(taskId)
  expect(url.searchParams.get('limit')).toBe('20')
  expect(url.searchParams.get('cursor')).toBe(cursor)
  expect(reader.state.history.data).toEqual({ items: [], next_cursor: null })
  expect(reader.state.history.loaded).toBe(true)
  expect(reader.state.history.error).toBe('')
})

test.each(['context', 'history'] as const)(
  '%s refuses unauthenticated, unpermitted, hidden-case and malformed objects before fetching',
  async (slot) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const { session, reader } = setup()
    const original = session.state.user!
    for (const mode of [
      'no-user',
      'no-permission',
      'hidden-case',
      'invalid-case',
      'invalid-task',
    ]) {
      session.state.user = { ...original, permissions: ['review.read'], case_ids: [caseId] }
      if (mode === 'no-user') session.state.user = null
      if (mode === 'no-permission') session.state.user!.permissions = []
      if (mode === 'hidden-case') session.state.user!.case_ids = []
      await (slot === 'context' ? reader.loadContext : reader.loadHistory)(
        mode === 'invalid-case' ? '../case' : caseId,
        mode === 'invalid-task' ? '../task' : taskId,
      )
      expect(reader.state[slot].loaded).toBe(false)
      expect(reader.state[slot].data).toBeNull()
      expect(reader.state[slot].error).not.toBe('')
    }
    expect(fetch).not.toHaveBeenCalled()
  },
)

test.each(['', 'a'.repeat(129)])(
  'rejects an out-of-contract cursor before fetching: %j',
  async (cursor) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const { reader } = setup()
    await reader.loadHistory(caseId, taskId, cursor)
    expect(fetch).not.toHaveBeenCalled()
    expect(reader.state.history.error).not.toBe('')
  },
)

test.each([
  { task_id: otherTaskId },
  { run_version: 0 },
  { result_version: 1.5 },
  { object_version: Number.MAX_SAFE_INTEGER + 1 },
  { review_version: -1 },
  { policy_version: '' },
  { policy_version: 'a'.repeat(129) },
  { snapshot_sha256: 'A'.repeat(64) },
  { snapshot_sha256: 'a'.repeat(63) },
  { unexpected: 'not-in-contract' },
])('rejects malformed or cross-task context: %j', async (change) => {
  vi.stubGlobal('fetch', async () => Response.json({ ...context(), ...change }))
  const { reader } = setup()
  await reader.loadContext(caseId, taskId)
  expect(reader.state.context.data).toBeNull()
  expect(reader.state.context.loaded).toBe(false)
  expect(reader.state.context.error).toContain('已拒绝显示')
})

test.each(Object.keys(context()))('requires the context field %s', async (field) => {
  const data: Record<string, unknown> = context()
  delete data[field]
  vi.stubGlobal('fetch', async () => Response.json(data))
  const { reader } = setup()
  await reader.loadContext(caseId, taskId)
  expect(reader.state.context.data).toBeNull()
  expect(reader.state.context.loaded).toBe(false)
})

test.each([
  { task_id: otherTaskId },
  { review_id: 'invalid' },
  { reviewer_id: null },
  { run_version: 0 },
  { result_version: 1.5 },
  { expected_review_version: -1 },
  { review_version: 0 },
  { review_version: Number.MAX_SAFE_INTEGER + 1 },
  { decision: 'approved' },
  { reason: '' },
  { reason: 'a'.repeat(4097) },
  { policy_version: '' },
  { policy_version: 'a'.repeat(129) },
  { evidence_ids: [] },
  { evidence_ids: ['invalid'] },
  { evidence_ids: [evidenceId, evidenceId] },
  { evidence_ids: [evidenceId, evidenceId.toUpperCase()] },
  { created_at: '2026-10-22' },
  { created_at: '2026-02-30T01:02:03Z' },
  { created_at: '2026-10-22T24:00:00Z' },
  { created_at: '2026-10-22T01:02:03+24:00' },
  { unexpected: 'not-in-contract' },
])('rejects malformed or cross-task historical review: %j', async (change) => {
  vi.stubGlobal('fetch', async () =>
    Response.json({ items: [{ ...review(), ...change }], next_cursor: null }),
  )
  const { reader } = setup()
  await reader.loadHistory(caseId, taskId)
  expect(reader.state.history.data).toBeNull()
  expect(reader.state.history.loaded).toBe(false)
  expect(reader.state.history.error).toContain('已拒绝显示')
})

test.each(Object.keys(review()))('requires the historical review field %s', async (field) => {
  const data: Record<string, unknown> = review()
  delete data[field]
  vi.stubGlobal('fetch', async () => Response.json({ items: [data], next_cursor: null }))
  const { reader } = setup()
  await reader.loadHistory(caseId, taskId)
  expect(reader.state.history.data).toBeNull()
  expect(reader.state.history.loaded).toBe(false)
})

test.each([
  null,
  { items: [] },
  { items: null, next_cursor: null },
  { items: [], next_cursor: '' },
  { items: [], next_cursor: 'a'.repeat(129) },
  { items: [], next_cursor: null, unexpected: true },
])('a malformed page is not converted to an empty successful history: %j', async (data) => {
  vi.stubGlobal('fetch', async () => Response.json(data))
  const { reader } = setup()
  await reader.loadHistory(caseId, taskId)
  expect(reader.state.history.data).toBeNull()
  expect(reader.state.history.loaded).toBe(false)
  expect(reader.state.history.error).not.toBe('')
})

test.each([
  'confirm_candidate',
  'reject_candidate',
  'return_for_evidence',
  'request_rerun',
] as const)(
  'displays the actual %s decision without inferring approved actions',
  async (decision) => {
    vi.stubGlobal('fetch', async () =>
      Response.json({ items: [{ ...review(), decision }], next_cursor: null }),
    )
    const { reader } = setup()
    await reader.loadHistory(caseId, taskId)
    expect(reader.state.history.data?.items[0]?.decision).toBe(decision)
    expect(reader.state.context.loaded).toBe(false)
  },
)

test.each([403, 404, 503])(
  'a %s response clears old results and keeps context/history errors distinct',
  async (status) => {
    let failing = false
    vi.stubGlobal('fetch', async (url: string) =>
      failing
        ? Response.json(
            { code: 'DEPENDENCY_NOT_READY', detail: 'private upstream details' },
            { status },
          )
        : Response.json(url.includes('review-context') ? context() : page()),
    )
    const { reader } = setup()
    await reader.loadContext(caseId, taskId)
    await reader.loadHistory(caseId, taskId)
    failing = true
    await reader.loadContext(caseId, taskId)
    expect(reader.state.context.data).toBeNull()
    expect(reader.state.context.loaded).toBe(false)
    expect(reader.state.context.error).toContain('DEPENDENCY_NOT_READY')
    expect(reader.state.context.error).not.toContain('private upstream')
    expect(reader.state.history.loaded).toBe(true)
    await reader.loadHistory(caseId, taskId)
    expect(reader.state.history.data).toBeNull()
    expect(reader.state.history.loaded).toBe(false)
    expect(reader.state.history.error).toContain('DEPENDENCY_NOT_READY')
    expect(reader.state.history.error).not.toContain('private upstream')
    failing = false
    await reader.loadHistory(caseId, taskId)
    expect(reader.state.history.loaded).toBe(true)
  },
)

test.each([
  'generation',
  'user',
  'org',
  'role',
  'permission',
  'case-membership',
  'logout',
  'clear',
  'dispose',
])(
  'identity or lifetime change immediately clears both slots and rejects late success and error: %s',
  async (mode) => {
    const replies: ((response: Response) => void)[] = []
    vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => replies.push(resolve)))
    const { reader, session } = setup()
    const pendingContext = reader.loadContext(caseId, taskId)
    const pendingHistory = reader.loadHistory(caseId, taskId)
    expect(reader.state.context.busy).toBe(true)
    expect(reader.state.history.busy).toBe(true)
    if (mode === 'generation') session.state.generation++
    if (mode === 'user') session.state.user!.user_id = orgId
    if (mode === 'org') session.state.user!.org_id = userId
    if (mode === 'role') session.state.user!.roles = ['auditor']
    if (mode === 'permission') session.state.user!.permissions = []
    if (mode === 'case-membership') session.state.user!.case_ids = [otherCaseId]
    if (mode === 'logout') session.state.user = null
    if (mode === 'clear') reader.clear()
    if (mode === 'dispose') reader.dispose()
    expect(reader.state.context.busy).toBe(false)
    expect(reader.state.history.busy).toBe(false)
    replies[0]!(Response.json(context()))
    replies[1]!(Response.json({ code: 'DEPENDENCY_NOT_READY' }, { status: 503 }))
    await Promise.all([pendingContext, pendingHistory])
    for (const slot of [reader.state.context, reader.state.history]) {
      expect(slot.data).toBeNull()
      expect(slot.loaded).toBe(false)
      expect(slot.busy).toBe(false)
      expect(slot.error).toBe('')
    }
  },
)

test.each(['generation', 'user', 'org', 'role', 'permission', 'case-membership', 'logout'])(
  'changing %s clears already displayed context and history synchronously',
  async (mode) => {
    vi.stubGlobal('fetch', async (url: string) =>
      Response.json(url.includes('review-context') ? context() : page()),
    )
    const { reader, session } = setup()
    await reader.loadContext(caseId, taskId)
    await reader.loadHistory(caseId, taskId)
    expect(reader.state.context.loaded).toBe(true)
    expect(reader.state.history.loaded).toBe(true)
    if (mode === 'generation') session.state.generation++
    if (mode === 'user') session.state.user!.user_id = orgId
    if (mode === 'org') session.state.user!.org_id = userId
    if (mode === 'role') session.state.user!.roles.push('auditor')
    if (mode === 'permission') session.state.user!.permissions.push('task.read')
    if (mode === 'case-membership') session.state.user!.case_ids.pop()
    if (mode === 'logout') session.state.user = null
    for (const slot of [reader.state.context, reader.state.history]) {
      expect(slot.data).toBeNull()
      expect(slot.loaded).toBe(false)
      expect(slot.busy).toBe(false)
      expect(slot.error).toBe('')
    }
  },
)

test.each(['case', 'task'])(
  'changing %s invalidates both old requests and preserves new results',
  async (change) => {
    const replies: ((response: Response) => void)[] = []
    vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => replies.push(resolve)))
    const { reader } = setup()
    const oldContext = reader.loadContext(caseId, taskId)
    const oldHistory = reader.loadHistory(caseId, taskId)
    const nextCase = change === 'case' ? otherCaseId : caseId
    const nextTask = change === 'task' ? otherTaskId : taskId
    const newHistory = reader.loadHistory(nextCase, nextTask)
    expect(reader.state.context.busy).toBe(false)
    replies[2]!(Response.json(page(nextTask)))
    await newHistory
    replies[0]!(Response.json(context()))
    replies[1]!(Response.json({ code: 'OLD_RESPONSE' }, { status: 403 }))
    await Promise.all([oldContext, oldHistory])
    expect(reader.state.context.data).toBeNull()
    expect(reader.state.context.loaded).toBe(false)
    expect(reader.state.history.data).toEqual(page(nextTask))
    expect(reader.state.history.error).toBe('')
  },
)

test('a later page wins over both a pending first page and its late failure', async () => {
  const replies: ((response: Response) => void)[] = []
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => replies.push(resolve)))
  const { reader } = setup()
  const old = reader.loadHistory(caseId, taskId)
  const next = reader.loadHistory(caseId, taskId, 'next-page')
  replies[1]!(Response.json({ items: [], next_cursor: null }))
  await next
  replies[0]!(Response.json({ code: 'OLD_RESPONSE' }, { status: 503 }))
  await old
  expect(reader.state.history.data).toEqual({ items: [], next_cursor: null })
  expect(reader.state.history.loaded).toBe(true)
  expect(reader.state.history.error).toBe('')
})

test('a cleared history success and context error cannot restore disposed results', async () => {
  const replies: ((response: Response) => void)[] = []
  vi.stubGlobal('fetch', () => new Promise<Response>((resolve) => replies.push(resolve)))
  const { reader } = setup()
  const oldContext = reader.loadContext(caseId, taskId)
  const oldHistory = reader.loadHistory(caseId, taskId)
  reader.dispose()
  replies[0]!(Response.json({ code: 'OLD_RESPONSE' }, { status: 404 }))
  replies[1]!(Response.json(page()))
  await Promise.all([oldContext, oldHistory])
  for (const slot of [reader.state.context, reader.state.history]) {
    expect(slot.data).toBeNull()
    expect(slot.loaded).toBe(false)
    expect(slot.error).toBe('')
  }
  await reader.loadHistory(caseId, taskId)
  expect(replies).toHaveLength(2)
})

test('an invalid new selection clears previously loaded context and history', async () => {
  const fetch = vi.fn(async (url: string) =>
    Response.json(url.includes('review-context') ? context() : page()),
  )
  vi.stubGlobal('fetch', fetch)
  const { reader } = setup()
  await reader.loadContext(caseId, taskId)
  await reader.loadHistory(caseId, taskId)
  await reader.loadContext(caseId, '../invalid')
  expect(fetch).toHaveBeenCalledTimes(2)
  expect(reader.state.context.data).toBeNull()
  expect(reader.state.history.data).toBeNull()
  expect(reader.state.context.error).not.toBe('')
  expect(reader.state.history.loaded).toBe(false)
})
