import { afterEach, expect, test, vi } from 'vitest'
import { reactive } from 'vue'
import { BusinessClient, type Schemas } from './api'
import { createTaskCancellation } from './task-cancel'

const taskId = '11111111-1111-4111-8111-111111111111'
const caseId = '22222222-2222-4222-8222-222222222222'
const approvalId = '33333333-3333-4333-8333-333333333333'
const execution: Schemas['TaskExecutionStatus'] = {
  task_id: taskId,
  case_id: caseId,
  state: 'RUNNING',
  run_version: 2,
  result_version: 0,
  version: 7,
  result_available: false,
}
const accepted: Schemas['Accepted'] = {
  task_id: taskId,
  state: 'CANCEL_REQUESTED',
  status_url: `/api/v1/analysis/tasks/${taskId}/execution`,
}
function connected(permissions = ['task.read', 'task.cancel']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-cancel-transport-token')
  const state = reactive({
    generation: 1,
    busy: false,
    message: '',
    user: {
      user_id: '44444444-4444-4444-8444-444444444444',
      org_id: '55555555-5555-4555-8555-555555555555',
      roles: ['self-owned-fixture'],
      permissions,
      case_ids: [caseId],
    } as Schemas['CurrentUser'] | null,
  })
  return {
    state,
    has: (permission: string) => state.user?.permissions.includes(permission) ?? false,
    call: client.call.bind(client),
  }
}
function response(value: unknown = execution, etag: string | null = '"execution-7"') {
  return Response.json(value, { headers: etag ? { ETag: etag } : {} })
}
function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => {
    resolve = done
  })
  return { promise, resolve }
}
afterEach(() => {
  vi.unstubAllGlobals()
})

test.each([[], ['task.read'], ['task.cancel']].map((permissions) => ({ permissions })))(
  'no cancellation request without both permissions: $permissions',
  async ({ permissions }) => {
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected(permissions))
    await control.inspect(taskId)
    await control.request('reason', '', true)
    expect(fetcher).not.toHaveBeenCalled()
    expect(control.canSubmit()).toBe(false)
  },
)

test.each(['CREATED', 'QUEUED', 'RUNNING', 'WAIT_REVIEW', 'REVIEWING', 'RETURNED'] as const)(
  'exact fresh versions/etag, approval, confirmation and acceptance for %s',
  async (state) => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(response({ ...execution, state }))
      .mockResolvedValueOnce(Response.json(accepted, { status: 202 }))
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    await control.request('  self-owned cancellation reason  ', approvalId, false)
    expect(fetcher).toHaveBeenCalledTimes(1)
    await control.request('  self-owned cancellation reason  ', approvalId, true)
    expect(fetcher).toHaveBeenCalledTimes(2)
    const [url, options] = fetcher.mock.calls[1] as [string, RequestInit]
    expect(url).toContain(`/analysis/tasks/${taskId}/cancel`)
    expect(options.method).toBe('POST')
    expect(new Headers(options.headers).get('If-Match')).toBe('"execution-7"')
    expect(new Headers(options.headers).get('Idempotency-Key')).toBeTruthy()
    expect(JSON.parse(String(options.body))).toEqual({
      reason: 'self-owned cancellation reason',
      approval_id: approvalId,
      expected_run_version: 2,
      expected_version: 7,
    })
    expect(control.state.accepted).toBe(true)
    expect(control.state.execution?.state).toBe(state)
    expect(control.canSubmit()).toBe(false)
  },
)

test.each(['SUCCEEDED', 'FAILED', 'ARCHIVED', 'CANCEL_REQUESTED', 'CANCELLED'] as const)(
  'terminal/nonrequestable state %s never posts',
  async (state) => {
    const fetcher = vi.fn().mockResolvedValue(response({ ...execution, state }))
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    await control.request('reason', '', true)
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(control.canSubmit()).toBe(false)
  },
)

test.each(['task', 'case', 'run', 'version', 'etag', 'weak-etag'] as const)(
  'invalid execution binding %s blocks cancellation',
  async (defect) => {
    const data = { ...execution }
    if (defect === 'task') data.task_id = approvalId
    if (defect === 'case') data.case_id = approvalId
    if (defect === 'run') data.run_version = 0
    if (defect === 'version') data.version = 1.5
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          response(data, defect === 'etag' ? null : defect === 'weak-etag' ? 'W/"v7"' : '"v7"'),
        ),
    )
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    expect(control.state.execution).toBeNull()
    expect(control.canSubmit()).toBe(false)
  },
)

test.each(['reason', 'approval', 'too-long'])(
  'invalid form %s sends no mutation',
  async (defect) => {
    const fetcher = vi.fn().mockResolvedValue(response())
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    await control.request(
      defect === 'reason' ? '   ' : defect === 'too-long' ? 'x'.repeat(4097) : 'reason',
      defect === 'approval' ? 'wrong-id' : '',
      true,
    )
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(control.state.pending).toBe(false)
  },
)

test.each(['network', 'server', 'receipt'] as const)(
  'ambiguous %s retries exact body/key/etag without another read',
  async (fault) => {
    const fetcher = vi.fn().mockResolvedValueOnce(response())
    if (fault === 'network') fetcher.mockRejectedValueOnce(new Error('private transport detail'))
    if (fault === 'server')
      fetcher.mockResolvedValueOnce(
        Response.json({ code: 'INTERNAL_ERROR', detail: 'private detail' }, { status: 500 }),
      )
    if (fault === 'receipt')
      fetcher.mockResolvedValueOnce(
        Response.json({ ...accepted, status_url: 'https://untrusted.example/' }, { status: 202 }),
      )
    fetcher.mockResolvedValueOnce(Response.json(accepted, { status: 202 }))
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    await control.request('immutable original reason', '', true)
    expect(control.state.uncertain).toBe(true)
    expect(control.state.accepted).toBe(false)
    expect(control.state.error).not.toContain('private')
    await control.inspect(taskId)
    await control.request('changed reason', approvalId, true)
    expect(fetcher).toHaveBeenCalledTimes(2)
    await control.retry()
    expect(fetcher).toHaveBeenCalledTimes(3)
    const [originalUrl, original] = fetcher.mock.calls[1] as [string, RequestInit]
    const [retryUrl, retry] = fetcher.mock.calls[2] as [string, RequestInit]
    expect(retryUrl).toBe(originalUrl)
    expect(retry.body).toBe(original.body)
    expect(retry.method).toBe(original.method)
    expect(retry.headers).toEqual(original.headers)
    expect(control.state.accepted).toBe(true)
    expect(control.state.pending).toBe(false)
  },
)

test.each([403, 404, 409, 412, 422, 428])(
  'definite refusal %s invalidates conditions without retrying',
  async (status) => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(response())
      .mockResolvedValueOnce(Response.json({ code: 'PERMISSION_REQUIRED' }, { status }))
    vi.stubGlobal('fetch', fetcher)
    const control = createTaskCancellation(connected())
    await control.inspect(taskId)
    await control.request('reason', '', true)
    await control.retry()
    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(control.state.uncertain).toBe(false)
    expect(control.state.execution).toBeNull()
  },
)

test.each(['generation', 'permission', 'case', 'user', 'role', 'reset'] as const)(
  'late read is discarded after %s changes',
  async (change) => {
    const pending = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(pending.promise))
    const session = connected()
    const control = createTaskCancellation(session)
    const reading = control.inspect(taskId)
    if (change === 'generation') session.state.generation++
    if (change === 'permission') session.state.user!.permissions = ['task.read']
    if (change === 'case') session.state.user!.case_ids = []
    if (change === 'user') session.state.user!.user_id = approvalId
    if (change === 'role') session.state.user!.roles = ['changed-role']
    if (change === 'reset') control.reset()
    pending.resolve(response())
    await reading
    expect(control.state.execution).toBeNull()
    expect(control.state.busy).toBe(false)
  },
)

test('identity switch during POST discards late acceptance and duplicate clicks do not post twice', async () => {
  const pending = deferred<Response>()
  const fetcher = vi.fn().mockResolvedValueOnce(response()).mockReturnValueOnce(pending.promise)
  vi.stubGlobal('fetch', fetcher)
  const session = connected()
  const control = createTaskCancellation(session)
  await control.inspect(taskId)
  const posting = control.request('reason', '', true)
  await control.request('another reason', '', true)
  expect(fetcher).toHaveBeenCalledTimes(2)
  session.state.generation++
  pending.resolve(Response.json(accepted, { status: 202 }))
  await posting
  expect(control.state.accepted).toBe(false)
  expect(control.state.pending).toBe(false)
})
