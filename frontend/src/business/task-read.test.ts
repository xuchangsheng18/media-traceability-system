import { afterEach, expect, test, vi } from 'vitest'
import { BusinessClient, type Schemas } from './api'
import { createPendingReviewReader, createTaskReader, routeTaskId } from './task-read'

const taskId = '10000000-0000-4000-8000-000000000001'
const caseId = '20000000-0000-4000-8000-000000000001'
const otherCaseId = '20000000-0000-4000-8000-000000000002'
const assetId = '30000000-0000-4000-8000-000000000001'
const binding = { taskId, runVersion: 2, resultVersion: 7 }
const execution: Schemas['TaskExecutionStatus'] = {
  task_id: taskId,
  case_id: caseId,
  state: 'RUNNING',
  run_version: 2,
  result_version: 7,
  version: 8,
  result_available: false,
}
function snapshot(resultVersion = 7): Schemas['Task'] {
  return {
    task_id: taskId,
    case_id: caseId,
    asset_id: assetId,
    state: 'WAIT_REVIEW',
    run_version: 2,
    result_version: resultVersion,
    policy_version: 'self-owned-policy',
    version: 8,
    progress: 1,
    nodes: [],
    missing_modalities: [],
    report_eligibility: 'reviewable',
    created_at: '2026-10-21T00:00:00Z',
  }
}
function historyResponse(url: URL, override?: Record<string, string>) {
  const resultVersion = Number(url.searchParams.get('history[result_version]'))
  const headers = {
    'X-Task-Id': taskId,
    'X-Run-Version': '2',
    'X-Result-Version': String(resultVersion),
    ...override,
  }
  if (url.pathname.endsWith('/risk-findings') || url.pathname.endsWith('/forensics'))
    return Response.json(
      {
        binding: {
          task_id: taskId,
          run_version: 2,
          result_version: resultVersion,
          policy_version: 'self-owned-policy',
        },
        findings: [],
        missing_modalities: [],
        warnings: [],
      },
      { headers },
    )
  if (url.pathname.endsWith('/evidence'))
    return Response.json({ items: [], next_cursor: null }, { headers })
  if (url.pathname.endsWith('/timeline'))
    return Response.json(
      { asset_id: assetId, mapping_version: 'self-owned-map', items: [] },
      { headers },
    )
  return Response.json(snapshot(resultVersion), { headers })
}
function connected(permissions = ['task.read', 'evidence.read', 'asset.read', 'review.read']) {
  const client = new BusinessClient()
  client.replaceToken('self-owned-task-reader-token')
  return {
    call: client.call.bind(client),
    has: (permission: string) => permissions.includes(permission),
  }
}
function address(raw: string) {
  return new URL(raw, 'http://self-owned.invalid')
}
afterEach(() => vi.unstubAllGlobals())

test('all result endpoints bind exact history versions and timeline also binds the task', async () => {
  const requested: URL[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    requested.push(url)
    return historyResponse(url)
  })
  const reader = createTaskReader(connected())
  await reader.loadResults(binding)
  expect(reader.snapshot.state.data?.result_version).toBe(7)
  expect(reader.timeline.state.data?.asset_id).toBe(assetId)
  expect(requested.map((url) => url.pathname).sort()).toEqual(
    [
      `/business/api/v1/analysis/tasks/${taskId}`,
      `/business/api/v1/analysis/tasks/${taskId}/evidence`,
      `/business/api/v1/analysis/tasks/${taskId}/forensics`,
      `/business/api/v1/analysis/tasks/${taskId}/risk-findings`,
      `/business/api/v1/assets/${assetId}/timeline`,
    ].sort(),
  )
  for (const url of requested) {
    expect(url.searchParams.get('history[run_version]')).toBe('2')
    expect(url.searchParams.get('history[result_version]')).toBe('7')
    expect(url.searchParams.has('case_id')).toBe(false)
    expect(url.searchParams.get('history[task_id]')).toBe(
      url.pathname.endsWith('/timeline') ? taskId : null,
    )
  }
})

test.each([
  ['X-Task-Id', ''],
  ['X-Run-Version', ''],
  ['X-Result-Version', ''],
  ['X-Task-Id', otherCaseId],
  ['X-Run-Version', '3'],
  ['X-Result-Version', '8'],
])('a missing or mismatched %s header refuses every history result (%s)', async (name, value) => {
  vi.stubGlobal('fetch', async (raw: string) => {
    const response = historyResponse(address(raw), { [name]: value })
    if (!value) response.headers.delete(name)
    return response
  })
  const reader = createTaskReader(connected())
  await reader.loadResults(binding)
  for (const slot of [reader.snapshot, reader.risk, reader.forensics, reader.evidence]) {
    expect(slot.state.data).toBeNull()
    expect(slot.state.error).toMatch(/历史.*绑定/)
  }
  expect(reader.timeline.state.data).toBeNull()
})

test('timeline refuses its own mismatched historical binding', async () => {
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    return historyResponse(
      url,
      url.pathname.endsWith('/timeline') ? { 'X-Run-Version': '9' } : undefined,
    )
  })
  const reader = createTaskReader(connected())
  await reader.loadResults(binding)
  expect(reader.snapshot.state.data?.task_id).toBe(taskId)
  expect(reader.timeline.state.data).toBeNull()
  expect(reader.timeline.state.error).toMatch(/历史.*绑定/)
})

test('matching headers cannot hide a different snapshot body version', async () => {
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    const response = historyResponse(url)
    return url.pathname.endsWith(taskId)
      ? Response.json(snapshot(8), { headers: response.headers })
      : response
  })
  const reader = createTaskReader(connected())
  await reader.loadResults(binding)
  expect(reader.snapshot.state.data).toBeNull()
  expect(reader.snapshot.state.error).toMatch(/历史.*绑定/)
})

test('live execution remains available without a snapshot and selects current-run records exactly', async () => {
  const requested: URL[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    requested.push(url)
    if (url.pathname.endsWith('/execution')) return Response.json(execution)
    if (url.pathname.endsWith('/nodes'))
      return Response.json({ task_id: taskId, run_version: 2, items: [] })
    if (url.pathname.endsWith('/events')) return Response.json({ items: [], next_cursor: 'a+b/c=' })
    throw new Error('No history fallback permitted')
  })
  const reader = createTaskReader(connected())
  await reader.observe(taskId)
  expect(reader.execution.state.data?.result_available).toBe(false)
  expect(reader.nodes.state.data?.items).toEqual([])
  expect(reader.snapshot.state.loaded).toBe(false)
  await reader.loadEvents(true)
  expect(requested.map((url) => url.search)).toEqual([
    '',
    '?run_version=2',
    '?run_version=2&limit=20',
    '?run_version=2&limit=20&cursor=a%2Bb%2Fc%3D',
  ])
})

test('same-task refresh rejects a late older execution and does not launch its run queries', async () => {
  let finish!: (response: Response) => void
  let executions = 0
  const runs: string[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    if (url.pathname.endsWith('/execution')) {
      executions++
      if (executions === 1)
        return new Promise<Response>((resolve) => {
          finish = resolve
        })
      return Response.json({ ...execution, run_version: 3 })
    }
    runs.push(url.searchParams.get('run_version') ?? '')
    if (url.pathname.endsWith('/nodes'))
      return Response.json({ task_id: taskId, run_version: 3, items: [] })
    return Response.json({ items: [], next_cursor: null })
  })
  const reader = createTaskReader(connected())
  const older = reader.observe(taskId)
  await reader.observe(taskId)
  finish(Response.json(execution))
  await older
  expect(reader.execution.state.data?.run_version).toBe(3)
  expect(runs).toEqual(['3', '3'])
})

test('a reused selection object and late older result cannot replace a newer same-task version', async () => {
  let finish!: (response: Response) => void
  const timelineVersions: string[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    if (url.pathname.endsWith('/timeline'))
      timelineVersions.push(url.searchParams.get('history[result_version]') ?? '')
    if (url.pathname.endsWith(taskId) && url.searchParams.get('history[result_version]') === '7')
      return new Promise<Response>((resolve) => {
        finish = resolve
      })
    return historyResponse(url)
  })
  const reader = createTaskReader(connected())
  const selected = { ...binding }
  const older = reader.loadResults(selected)
  selected.resultVersion = 8
  await reader.loadResults(selected)
  finish(
    historyResponse(
      address(`/analysis/tasks/${taskId}?history[run_version]=2&history[result_version]=7`),
    ),
  )
  await older
  expect(reader.snapshot.state.data?.result_version).toBe(8)
  expect(reader.risk.state.data?.binding.result_version).toBe(8)
  expect(reader.snapshot.state.error).toBe('')
  expect(timelineVersions).toEqual(['8'])
})

test('clearing the selection immediately hides results and invalidates late completion', async () => {
  let finish!: (response: Response) => void
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    if (url.pathname.endsWith(taskId))
      return new Promise<Response>((resolve) => {
        finish = resolve
      })
    return historyResponse(url)
  })
  const reader = createTaskReader(connected())
  const reading = reader.loadResults(binding)
  reader.reset()
  finish(
    historyResponse(
      address(`/analysis/tasks/${taskId}?history[run_version]=2&history[result_version]=7`),
    ),
  )
  await reading
  expect(reader.snapshot.state.data).toBeNull()
  expect(reader.snapshot.state.loaded).toBe(false)
  expect(reader.risk.state.data).toBeNull()
  expect(reader.timeline.state.data).toBeNull()
})

test('result permissions and server denial remain independent of an available task snapshot', async () => {
  const requested: string[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    const url = address(raw)
    requested.push(url.pathname)
    if (url.pathname.endsWith('/risk-findings'))
      return Response.json({ code: 'SOURCE_ACCESS_DENIED' }, { status: 403 })
    return historyResponse(url)
  })
  const reader = createTaskReader(connected(['task.read']))
  await reader.loadResults(binding)
  expect(reader.snapshot.state.data?.task_id).toBe(taskId)
  expect(reader.risk.state.error).toContain('SOURCE_ACCESS_DENIED')
  expect(reader.evidence.state.error).toContain('权限')
  expect(reader.timeline.state.error).toContain('权限')
  expect(requested.some((path) => path.endsWith('/evidence') || path.endsWith('/timeline'))).toBe(
    false,
  )
})

test.each([0, -1, 1.5, Number.NaN, Number.POSITIVE_INFINITY])(
  'invalid history version %s never reaches transport',
  async (version) => {
    const requested: string[] = []
    vi.stubGlobal('fetch', async (raw: string) => {
      requested.push(raw)
      return Response.json({})
    })
    const reader = createTaskReader(connected())
    await reader.loadResults({ ...binding, resultVersion: version })
    expect(requested).toEqual([])
    expect(reader.snapshot.state.data).toBeNull()
    expect(reader.snapshot.state.error).not.toBe('')
  },
)

test('pending queue case changes discard stale data and keep cursor bound to the queried case', async () => {
  let finish!: (response: Response) => void
  const requested: string[] = []
  vi.stubGlobal('fetch', async (raw: string) => {
    requested.push(raw)
    if (address(raw).searchParams.get('case_id') === caseId)
      return new Promise<Response>((resolve) => {
        finish = resolve
      })
    return Response.json({ items: [], next_cursor: null })
  })
  const reader = createPendingReviewReader(connected())
  const older = reader.load(caseId)
  reader.clear()
  await reader.load(otherCaseId, 'a+b/c=')
  finish(
    Response.json({
      items: [
        {
          task_id: taskId,
          case_id: caseId,
          task_state: 'WAIT_REVIEW',
          availability: 'RESULT_UNAVAILABLE',
          context: null,
        },
      ],
      next_cursor: 'old',
    }),
  )
  await older
  expect(reader.state.data).toEqual({ items: [], next_cursor: null })
  expect(requested[1]).toBe(
    `/business/api/v1/reviews/pending?case_id=${otherCaseId}&limit=20&cursor=a%2Bb%2Fc%3D`,
  )
})

test('queue preserves READY, RESULT_UNAVAILABLE, and SOURCE_BLOCKED without invented review context', async () => {
  const context: Schemas['ReviewContext'] = {
    task_id: taskId,
    run_version: 2,
    result_version: 7,
    policy_version: 'self-owned-policy',
    snapshot_sha256: 'a'.repeat(64),
    object_version: 8,
    review_version: 0,
  }
  const items: Schemas['PendingReviewItem'][] = [
    { task_id: taskId, case_id: caseId, task_state: 'WAIT_REVIEW', availability: 'READY', context },
    {
      task_id: taskId,
      case_id: caseId,
      task_state: 'RETURNED',
      availability: 'RESULT_UNAVAILABLE',
      context: null,
    },
    {
      task_id: taskId,
      case_id: caseId,
      task_state: 'REVIEWING',
      availability: 'SOURCE_BLOCKED',
      context: null,
    },
  ]
  vi.stubGlobal('fetch', async () => Response.json({ items, next_cursor: null }))
  const reader = createPendingReviewReader(connected())
  await reader.load(caseId)
  expect(reader.state.data?.items).toEqual(items)
})

test('queue error is distinct from a successful empty page and clears previous data', async () => {
  let failure = false
  vi.stubGlobal('fetch', async () =>
    failure
      ? Response.json({ code: 'FORMAL_POLICY_UNCONFIGURED' }, { status: 503 })
      : Response.json({ items: [], next_cursor: null }),
  )
  const reader = createPendingReviewReader(connected())
  await reader.load(caseId)
  expect(reader.state.loaded).toBe(true)
  expect(reader.state.error).toBe('')
  failure = true
  await reader.load(caseId)
  expect(reader.state.data).toBeNull()
  expect(reader.state.loaded).toBe(false)
  expect(reader.state.error).toContain('FORMAL_POLICY_UNCONFIGURED')
})

test.each([
  undefined,
  ['10000000-0000-4000-8000-000000000001'],
  '../task',
  'self-owned-token',
  `${taskId}?token=x`,
])('untrusted route task selection %s is ignored', (value) => {
  expect(routeTaskId(value)).toBe('')
})
test('one validated UUID may prefill the task input', () => {
  expect(routeTaskId(taskId)).toBe(taskId)
})
