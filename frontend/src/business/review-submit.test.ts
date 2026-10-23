import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import { createReviewSubmitter } from './review-submit'

const caseId = '20000000-0000-4000-8000-000000000001'
const taskId = '30000000-0000-4000-8000-000000000001'
const userId = '40000000-0000-4000-8000-000000000001'
const evidenceId = '60000000-0000-4000-8000-000000000001'
const etag = '"server-context-exact-opaque"'
const context: Schemas['ReviewContext'] = {
  task_id: taskId,
  run_version: 3,
  result_version: 4,
  policy_version: 'self-owned-policy/2',
  snapshot_sha256: 'a'.repeat(64),
  object_version: 5,
  review_version: 6,
}
const body: Schemas['ReviewCreate'] = {
  task_id: taskId,
  run_version: 3,
  result_version: 4,
  policy_version: context.policy_version,
  expected_review_version: 6,
  decision: 'return_for_evidence',
  reason: 'self-owned observation',
  evidence_ids: [evidenceId],
}
function receipt(): Schemas['Review'] {
  return {
    ...body,
    review_id: '70000000-0000-4000-8000-000000000001',
    reviewer_id: userId,
    review_version: 7,
    created_at: '2026-10-22T08:00:00+08:00',
  }
}
const controls: ReturnType<typeof createReviewSubmitter>[] = []
function setup() {
  const client = new BusinessClient()
  client.replaceToken('self-owned-review-write-transport')
  const session = {
    state: reactive({
      generation: 1,
      user: {
        user_id: userId,
        org_id: '50000000-0000-4000-8000-000000000001',
        roles: ['business_reviewer'],
        permissions: ['review.read', 'review.perform'],
        case_ids: [caseId],
      } as Schemas['CurrentUser'] | null,
    }),
    has: (permission: string) => session.state.user?.permissions.includes(permission) ?? false,
    call: client.call.bind(client),
  }
  const selection = reactive({
    caseId,
    taskId,
    context: { ...context } as Schemas['ReviewContext'] | null,
    etag: etag as string | null,
  })
  const control = createReviewSubmitter(session, () => selection)
  Object.assign(control.draft, {
    decision: body.decision,
    reason: body.reason,
    evidenceIds: evidenceId,
    confirmed: true,
  })
  controls.push(control)
  return { session, selection, control }
}
afterEach(() => {
  controls.splice(0).forEach((control) => control.dispose())
  vi.unstubAllGlobals()
})

test('freezes the exact server context, opaque etag and intended fields; receipt only acknowledges append', async () => {
  const fetcher = vi.fn(async () => Response.json(receipt(), { status: 201 }))
  vi.stubGlobal('fetch', fetcher)
  const { control } = setup()
  await control.submit()
  const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit]
  expect(url).toBe('/business/api/v1/reviews')
  expect(init.method).toBe('POST')
  expect(JSON.parse(String(init.body))).toEqual(body)
  expect(new Headers(init.headers).get('If-Match')).toBe(etag)
  expect(new Headers(init.headers).get('Idempotency-Key')).toMatch(/^[a-f0-9-]{36}$/)
  expect(control.state.receipt).toEqual(receipt())
  expect(control.canSubmit()).toBe(false)
  expect(control.state.message).toContain('追加')
})

test.each([
  'missing-read',
  'missing-perform',
  'hidden-case',
  'anonymous',
  'no-context',
  'no-etag',
  'weak-etag',
  'wrong-task',
  'bad-version',
  'no-confirmation',
  'no-reason',
  'too-long',
  'no-evidence',
  'duplicate-evidence',
  'bad-evidence',
  'bad-decision',
])('%s cannot send a write', async (defect) => {
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  const { control, selection, session } = setup()
  if (defect === 'missing-read') session.state.user!.permissions = ['review.perform']
  if (defect === 'missing-perform') session.state.user!.permissions = ['review.read']
  if (defect === 'hidden-case') session.state.user!.case_ids = []
  if (defect === 'anonymous') session.state.user = null
  if (defect === 'no-context') selection.context = null
  if (defect === 'no-etag') selection.etag = null
  if (defect === 'weak-etag') selection.etag = 'W/"weak"'
  if (defect === 'wrong-task') selection.context!.task_id = evidenceId
  if (defect === 'bad-version') selection.context!.review_version = -1
  if (defect === 'no-confirmation') control.draft.confirmed = false
  if (defect === 'no-reason') control.draft.reason = '   '
  if (defect === 'too-long') control.draft.reason = '文'.repeat(4097)
  if (defect === 'no-evidence') control.draft.evidenceIds = ''
  if (defect === 'duplicate-evidence')
    control.draft.evidenceIds = `${evidenceId},${evidenceId.toUpperCase()}`
  if (defect === 'bad-evidence') control.draft.evidenceIds = '../evidence'
  if (defect === 'bad-decision') control.draft.decision = 'approved'
  await control.submit()
  expect(fetcher).not.toHaveBeenCalled()
  expect(control.state.receipt).toBeNull()
})

test.each([408, 429, 500, 503, 'network', 'invalid-receipt'] as const)(
  '%s preserves one immutable request for explicit retry only',
  async (fault) => {
    const fetcher = vi
      .fn()
      .mockImplementationOnce(async () => {
        if (fault === 'network') throw new TypeError('network unavailable')
        return fault === 'invalid-receipt'
          ? Response.json({ ...receipt(), reviewer_id: evidenceId })
          : Response.json({ code: 'TEST_ONLY_FAILURE' }, { status: fault })
      })
      .mockResolvedValueOnce(Response.json(receipt()))
    vi.stubGlobal('fetch', fetcher)
    const { control } = setup()
    await control.submit()
    expect(control.state.uncertain).toBe(true)
    expect(control.canEdit()).toBe(false)
    control.draft.reason = 'external mutation cannot replace frozen intent'
    await control.submit()
    expect(fetcher).toHaveBeenCalledTimes(1)
    await control.retry()
    expect(fetcher).toHaveBeenCalledTimes(2)
    const first = fetcher.mock.calls[0]![1] as RequestInit
    const second = fetcher.mock.calls[1]![1] as RequestInit
    expect(second.body).toBe(first.body)
    expect(new Headers(second.headers).get('Idempotency-Key')).toBe(
      new Headers(first.headers).get('Idempotency-Key'),
    )
    expect(new Headers(second.headers).get('If-Match')).toBe(etag)
    expect(control.state.receipt).toEqual(receipt())
  },
)

test.each([400, 401, 403, 404, 409, 412, 422, 428])(
  '%s invalidates the write condition until context is reread',
  async (status) => {
    const fetcher = vi.fn(async () => Response.json({ code: 'TEST_ONLY_REFUSAL' }, { status }))
    vi.stubGlobal('fetch', fetcher)
    const { control } = setup()
    await control.submit()
    await control.submit()
    await control.retry()
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(control.state.uncertain).toBe(false)
    expect(control.state.stale).toBe(true)
    expect(control.canSubmit()).toBe(false)
  },
)

test.each([
  'user',
  'unit',
  'role',
  'permission',
  'case-membership',
  'generation',
  'context',
  'context-read-start',
  'case',
  'task',
  'etag',
  'dispose',
])('%s clears draft and ignores an already pending late response', async (change) => {
  let finish!: (value: Response) => void
  vi.stubGlobal(
    'fetch',
    () =>
      new Promise<Response>((resolve) => {
        finish = resolve
      }),
  )
  const { control, selection, session } = setup()
  const sending = control.submit()
  if (change === 'user') session.state.user!.user_id = evidenceId
  if (change === 'unit') session.state.user!.org_id = evidenceId
  if (change === 'role') session.state.user!.roles.push('system_admin')
  if (change === 'permission') session.state.user!.permissions.pop()
  if (change === 'case-membership') session.state.user!.case_ids.push(evidenceId)
  if (change === 'generation') session.state.generation++
  if (change === 'context') selection.context!.review_version++
  if (change === 'context-read-start') selection.context = null
  if (change === 'case') selection.caseId = evidenceId
  if (change === 'task') selection.taskId = evidenceId
  if (change === 'etag') selection.etag = '"another-server-tag"'
  if (change === 'dispose') control.dispose()
  expect(control.draft.reason).toBe('')
  finish(Response.json(receipt()))
  await sending
  expect(control.state.receipt).toBeNull()
  expect(control.state.error).toBe('')
  expect(control.state.uncertain).toBe(false)
})

test.each([
  'task',
  'reviewer',
  'run',
  'result',
  'policy',
  'expected-version',
  'version',
  'decision',
  'reason',
  'evidence',
  'extra-field',
  'invalid-created-at',
])('a %s mismatch never confirms the receipt and retains the original request', async (defect) => {
  const altered: Record<string, unknown> = { ...receipt() }
  if (defect === 'task') altered.task_id = evidenceId
  if (defect === 'reviewer') altered.reviewer_id = evidenceId
  if (defect === 'run') altered.run_version = 2
  if (defect === 'result') altered.result_version = 2
  if (defect === 'policy') altered.policy_version = 'old-policy'
  if (defect === 'expected-version') altered.expected_review_version = 5
  if (defect === 'version') altered.review_version = 6
  if (defect === 'decision') altered.decision = 'confirm_candidate'
  if (defect === 'reason') altered.reason = 'changed server reason'
  if (defect === 'evidence') altered.evidence_ids = [taskId]
  if (defect === 'extra-field') altered.approved = true
  if (defect === 'invalid-created-at') altered.created_at = '2026-02-30T00:00:00Z'
  vi.stubGlobal('fetch', async () => Response.json(altered))
  const { control } = setup()
  await control.submit()
  expect(control.state.receipt).toBeNull()
  expect(control.state.uncertain).toBe(true)
  expect(control.canEdit()).toBe(false)
})

test.each([
  'confirm_candidate',
  'reject_candidate',
  'return_for_evidence',
  'request_rerun',
] as const)('records %s only as the exact append decision', async (decision) => {
  vi.stubGlobal('fetch', async () => Response.json({ ...receipt(), decision }))
  const { control } = setup()
  control.draft.decision = decision
  await control.submit()
  expect(control.state.receipt?.decision).toBe(decision)
  expect(control.state.message).toContain('不表示批准')
})

test('Unicode limit counts code points and does not invent a smaller non-BMP budget', async () => {
  const reason = '🧪'.repeat(4096)
  vi.stubGlobal('fetch', async () => Response.json({ ...receipt(), reason }))
  const { control } = setup()
  control.draft.reason = reason
  expect(control.canSubmit()).toBe(true)
  await control.submit()
  expect(control.state.receipt?.reason).toBe(reason)
})

test('MAX_SAFE_INTEGER review version never sends an unsafe next version', async () => {
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  const { control, selection } = setup()
  selection.context!.review_version = Number.MAX_SAFE_INTEGER
  Object.assign(control.draft, {
    decision: body.decision,
    reason: body.reason,
    evidenceIds: evidenceId,
    confirmed: true,
  })
  expect(control.canSubmit()).toBe(false)
  await control.submit()
  expect(fetcher).not.toHaveBeenCalled()
})

test('an uncertain first request remains unresolved even if its replay receives 4xx', async () => {
  const fetcher = vi
    .fn()
    .mockRejectedValueOnce(new TypeError('network'))
    .mockResolvedValueOnce(Response.json({ code: 'TEST_ONLY_REFUSAL' }, { status: 403 }))
  vi.stubGlobal('fetch', fetcher)
  const { control } = setup()
  await control.submit()
  await control.retry()
  await control.submit()
  expect(fetcher).toHaveBeenCalledTimes(2)
  expect(control.state.receipt).toBeNull()
  expect(control.state.uncertain).toBe(true)
  expect(control.canEdit()).toBe(false)
})

test('repeated submission while the original request is running sends only one write', async () => {
  let finish!: (response: Response) => void
  const fetcher = vi.fn(
    () =>
      new Promise<Response>((done) => {
        finish = done
      }),
  )
  vi.stubGlobal('fetch', fetcher)
  const { control } = setup()
  const first = control.submit()
  await control.submit()
  await control.retry()
  expect(fetcher).toHaveBeenCalledTimes(1)
  finish(Response.json(receipt()))
  await first
  expect(control.state.receipt).toEqual(receipt())
})
