import { expect, test, type Page } from '@playwright/test'
import { createHash } from 'node:crypto'
import { createServer } from 'node:http'
import type { Schemas } from '../src/business/api'

// Source/Asset responses below are owned transport fixtures, not real authorization evidence.
function assetSourceFixture(): Schemas['Source'] {
  return {
    ...registeredSource(),
    source_id: catalogAsset().source_id,
    name: 'asset-source browser-owned record',
    authorization_status: 'verified',
    version: 4,
  }
}
async function openAssetSource(
  page: Page,
  permissions = ['asset.read', 'source.read'],
  loadCatalog = false,
) {
  await page.route(`**/business/api/v1/assets/${assetId}`, (route) =>
    route.fulfill({ json: catalogAsset() }),
  )
  await page.route(`**/business/api/v1/assets/${otherAssetId}`, (route) =>
    route.fulfill({ json: catalogAsset(otherAssetId) }),
  )
  await connectBusiness(page, permissions)
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await page.getByLabel('资产案件编号').fill(caseId)
  if (loadCatalog)
    await page.getByRole('button', { name: '查询资产／回到首页', exact: true }).click()
  await page.getByLabel('资产详情编号').fill(assetId)
  await page.getByRole('button', { name: '读取资产详情', exact: true }).click()
}

test('asset source panel reads exact metadata and reported states without enabling media use', async ({
  page,
}) => {
  const states = ['pending', 'verified', 'expired', 'revoked'] as const
  const requests: string[] = []
  await page.route(`**/business/api/v1/sources/${catalogAsset().source_id}`, (route) => {
    expect(route.request().method()).toBe('GET')
    expect(route.request().postData()).toBeNull()
    const state = states[requests.length]
    requests.push(route.request().url())
    return route.fulfill({ json: { ...assetSourceFixture(), authorization_status: state } })
  })
  await openAssetSource(page)
  const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
  await expect(panel.getByRole('button', { name: '读取来源授权明细', exact: true })).toBeEnabled()
  expect(requests).toHaveLength(0)
  for (const state of states) {
    await panel.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
    await expect(panel.getByTestId('asset-source-status-value')).toContainText(state)
  }
  await expect(panel.getByText('javascript:alert(1)', { exact: true })).toBeVisible()
  await expect(panel.locator('a[href]')).toHaveCount(0)
  await expect(panel.getByText('未提供', { exact: true })).toBeVisible()
  await expect(panel).toContainText('后续使用仍由服务端逐次授权')
  expect(requests).toHaveLength(4)
  expect(requests.every((url) => new URL(url).search === '')).toBe(true)
})

test('asset source panel requires independent source.read permission', async ({ page }) => {
  let requests = 0
  await page.route('**/business/api/v1/sources/**', (route) => {
    requests++
    return route.fulfill({ json: assetSourceFixture() })
  })
  await openAssetSource(page, ['asset.read'])
  const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
  await expect(panel.getByRole('button', { name: '读取来源授权明细', exact: true })).toBeDisabled()
  await expect(panel).toContainText('来源读取权限')
  expect(requests).toBe(0)
})

for (const field of ['source_id', 'case_id'] as const) {
  test(`asset source panel refuses a mismatched ${field} and clears the preceding record`, async ({
    page,
  }) => {
    let reads = 0
    await page.route('**/business/api/v1/sources/**', (route) => {
      reads++
      return route.fulfill({
        json:
          reads === 1 ? assetSourceFixture() : { ...assetSourceFixture(), [field]: otherCaseId },
      })
    })
    await openAssetSource(page)
    const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
    await panel.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
    await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toBeVisible()
    await panel.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
    await expect(panel.getByRole('status')).toContainText('拒绝显示')
    await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toHaveCount(0)
  })
}

test('asset source panel does not reuse a late record after switching assets with the same source', async ({
  page,
}) => {
  let release!: () => void
  const barrier = new Promise<void>((resolve) => {
    release = resolve
  })
  let began!: () => void
  const started = new Promise<void>((resolve) => {
    began = resolve
  })
  await page.route('**/business/api/v1/sources/**', async (route) => {
    began()
    await barrier
    await route.fulfill({ json: assetSourceFixture() })
  })
  await openAssetSource(page)
  await page.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
  await started
  await page.getByLabel('资产详情编号').fill(otherAssetId)
  await page.getByRole('button', { name: '读取资产详情', exact: true }).click()
  const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
  await expect(panel.getByRole('button', { name: '读取来源授权明细', exact: true })).toBeEnabled()
  const response = page.waitForResponse((reply) => reply.url().includes('/sources/'))
  release()
  await (await response).finished()
  await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toHaveCount(0)
  await expect(panel.getByRole('status')).toContainText('尚未读取')
})

test('asset source panel clears displayed authority when roles change without reconnect', async ({
  page,
}) => {
  await page.route('**/business/api/v1/sources/**', (route) =>
    route.fulfill({ json: assetSourceFixture() }),
  )
  await openAssetSource(page)
  const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
  await panel.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
  await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toBeVisible()
  await page.evaluate(() => {
    const root = document.getElementById('app') as HTMLElement & {
      _vnode?: { component?: { provides: Record<symbol, unknown> } }
    }
    const provides = root?._vnode?.component?.provides
    const key =
      provides &&
      Object.getOwnPropertySymbols(provides).find((item) => item.description === 'business-session')
    if (!provides || !key) throw new Error('SELF_OWNED_SESSION_FIXTURE_MISSING')
    const session = provides[key] as { state: { user: { roles: string[] } } }
    session.state.user.roles = ['self-owned-changed-role']
  })
  await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toHaveCount(0)
  await expect(panel).toHaveCount(0)
  await expect(page.locator('dl').filter({ hasText: '固定对象编号' })).toHaveCount(0)
})

type AssetContextChange = 'roles' | 'permissions' | 'case_ids' | 'user_id' | 'org_id' | 'user-null'
async function changeAssetContext(page: Page, field: AssetContextChange) {
  const generations = await page.evaluate((selected) => {
    const root = document.getElementById('app') as HTMLElement & {
      _vnode?: { component?: { provides: Record<symbol, unknown> } }
    }
    const provides = root?._vnode?.component?.provides
    const key =
      provides &&
      Object.getOwnPropertySymbols(provides).find((item) => item.description === 'business-session')
    if (!provides || !key) throw new Error('SELF_OWNED_SESSION_FIXTURE_MISSING')
    const session = provides[key] as {
      state: { generation: number; user: Schemas['CurrentUser'] | null }
    }
    const before = session.state.generation
    const user = session.state.user
    if (!user) throw new Error('SELF_OWNED_CONNECTED_FIXTURE_REQUIRED')
    if (selected === 'roles') user.roles.push('self-owned-new-role')
    else if (selected === 'permissions') user.permissions = ['source.read']
    else if (selected === 'case_ids') user.case_ids = []
    else if (selected === 'user_id') user.user_id = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
    else if (selected === 'org_id') user.org_id = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
    else session.state.user = null
    return [before, session.state.generation]
  }, field)
  expect(generations[1]).toBe(generations[0])
}

for (const field of ['roles', 'permissions', 'case_ids', 'user_id', 'org_id', 'user-null'] as const)
  test(`asset context clears loaded data on ${field} without changing generation`, async ({
    page,
  }) => {
    await page.route('**/business/api/v1/assets?**', (route) =>
      route.fulfill({ json: { items: [catalogAsset()], next_cursor: 'old-context-cursor' } }),
    )
    await page.route('**/business/api/v1/sources/**', (route) =>
      route.fulfill({ json: assetSourceFixture() }),
    )
    await openAssetSource(page, ['asset.read', 'asset.download', 'source.read'], true)
    const panel = page.getByRole('region', { name: '资产来源授权', exact: true })
    await panel.getByRole('button', { name: '读取来源授权明细', exact: true }).click()
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await expect(page.getByText('self-owned-fixed-v3', { exact: true })).toBeVisible()
    await expect(panel.getByText(assetSourceFixture().name, { exact: true })).toBeVisible()
    await changeAssetContext(page, field)
    await expect(page.locator('tbody tr')).toHaveCount(0)
    await expect(page.getByText('self-owned-fixed-v3', { exact: true })).toHaveCount(0)
    await expect(panel).toHaveCount(0)
    await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toHaveCount(0)
    await expect(page.getByRole('button', { name: '下一页资产', exact: true })).toBeDisabled()
  })

for (const target of ['list', 'detail'] as const)
  for (const outcome of ['success', 'error'] as const)
    test(`asset context discards late ${target} ${outcome} after role change`, async ({ page }) => {
      await openAssetSource(page)
      await expect(page.getByText('self-owned-fixed-v3', { exact: true })).toBeVisible()
      let release!: () => void
      const gate = new Promise<void>((resolve) => (release = resolve))
      let began!: () => void
      const started = new Promise<void>((resolve) => (began = resolve))
      let pending = true
      const path =
        target === 'list' ? '**/business/api/v1/assets?**' : `**/business/api/v1/assets/${assetId}`
      await page.route(path, async (route) => {
        if (pending) {
          began()
          await gate
        }
        const data =
          target === 'list'
            ? { items: [catalogAsset()], next_cursor: 'late-context-cursor' }
            : catalogAsset()
        await route.fulfill(
          outcome === 'error' && pending
            ? { status: 503, json: { code: 'SOURCE_AUTHORITY_UNAVAILABLE' } }
            : { json: data },
        )
      })
      const button = page.getByRole('button', {
        name: target === 'list' ? '查询资产／回到首页' : '读取资产详情',
        exact: true,
      })
      await button.click()
      await started
      const returned = page.waitForResponse((response) =>
        target === 'list'
          ? /\/assets\?/.test(response.url())
          : response.url().endsWith(`/assets/${assetId}`),
      )
      try {
        await changeAssetContext(page, 'roles')
        await expect(button).toBeEnabled()
      } finally {
        release()
      }
      await (await returned).finished()
      await expect(page.locator('tbody tr')).toHaveCount(0)
      await expect(page.locator('dl').filter({ hasText: '固定对象编号' })).toHaveCount(0)
      await expect(page.getByText('SOURCE_AUTHORITY_UNAVAILABLE', { exact: false })).toHaveCount(0)
      await expect(page.getByRole('button', { name: '下一页资产', exact: true })).toBeDisabled()
      // Current-context reads remain usable after the stale reply is discarded.
      pending = false
      await button.click()
      if (target === 'list') await expect(page.locator('tbody tr')).toHaveCount(1)
      else await expect(page.getByText('self-owned-fixed-v3', { exact: true })).toBeVisible()
    })

test('asset context role change prevents saving an already requested download', async ({
  page,
}) => {
  const { body, etag } = await openDownloadAsset(page)
  let release!: () => void
  const gate = new Promise<void>((resolve) => (release = resolve))
  let began!: () => void
  const started = new Promise<void>((resolve) => (began = resolve))
  const saved: string[] = []
  page.on('download', (download) => saved.push(download.suggestedFilename()))
  await page.route(`**/business/api/v1/assets/${assetId}/content`, async (route) => {
    began()
    await gate
    await route.fulfill({ body, contentType: 'application/octet-stream', headers: { ETag: etag } })
  })
  await page.getByRole('button', { name: '下载固定版本', exact: true }).click()
  await started
  const returned = page.waitForResponse((response) =>
    response.url().endsWith(`/assets/${assetId}/content`),
  )
  try {
    await changeAssetContext(page, 'roles')
    await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toHaveCount(0)
  } finally {
    release()
  }
  await (await returned).finished()
  await expect(page.getByText('已核验大小', { exact: false })).toHaveCount(0)
  expect(saved).toEqual([])
})

// Model rows are self-owned transport fixtures, never a trained-model claim.
const catalogModel: Schemas['Model'] = {
  model_id: '30000000-0000-4000-8000-000000000001',
  name: 'browser-owned model metadata',
  version: 'fixture/1',
  capability: 'media.ocr',
  digest: 'a'.repeat(64),
  dataset_version: 'fixture-data/1',
  model_card_ref: 'javascript:alert(1)',
  license_record_ref: 'controlled-license/1',
  backend: 'onnxruntime',
  environment_ref: 'controlled-environment/1',
  status: 'REGISTERED',
  row_version: 1,
}
const catalogEvaluation: Schemas['Evaluation'] = {
  evaluation_id: '40000000-0000-4000-8000-000000000001',
  model_id: catalogModel.model_id,
  dataset_id: 'fixture-data',
  dataset_version: 'fixture-data/1',
  protocol_id: 'fixture-protocol/1',
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
  artifact_ref: {
    object_id: catalogModel.model_id,
    version_id: 'immutable/1',
    sha256: 'b'.repeat(64),
  },
  created_at: '2026-10-21T00:00:00Z',
}

test('model page requires identity and model.read without sending directory requests', async ({
  page,
}) => {
  let requests = 0
  await page.route('**/business/api/v1/models?**', (route) => {
    requests++
    return route.fulfill({ json: { items: [], next_cursor: null } })
  })
  await page.goto('/#/models')
  await expect(page.getByRole('button', { name: '查询模型／回到首页' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '查询评测／回到首页' })).toBeDisabled()
  await connectBusiness(page, [])
  await page.getByRole('link', { name: '模型目录', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('没有模型目录读取权限')
  await expect(page.getByRole('button', { name: '查询模型／回到首页' })).toBeDisabled()
  expect(requests).toBe(0)
})

test('model page displays exact metadata and unknown metrics with independent pagination', async ({
  page,
}) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/models?**', (route) => {
    const url = new URL(route.request().url())
    requests.push(url.pathname + url.search)
    return route.fulfill({
      json: {
        items: url.searchParams.has('cursor') ? [] : [catalogModel],
        next_cursor: url.searchParams.has('cursor') ? null : 'a+b/c=',
      },
    })
  })
  await page.route('**/business/api/v1/model-evaluations?**', (route) =>
    route.fulfill({ json: { items: [catalogEvaluation], next_cursor: null } }),
  )
  await connectBusiness(page, ['model.read'])
  await page.getByRole('link', { name: '模型目录', exact: true }).click()
  await page.getByRole('button', { name: '查询模型／回到首页' }).click()
  await expect(page.getByRole('row').filter({ hasText: catalogModel.model_id })).toContainText(
    'REGISTERED',
  )
  await page.getByText('查看模型资料', { exact: true }).click()
  await expect(page.getByText('javascript:alert(1)', { exact: true })).toBeVisible()
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0)
  await page.getByRole('button', { name: '查询评测／回到首页' }).click()
  await page.getByText('查看评测指标', { exact: true }).click()
  await expect(
    page.getByRole('row').filter({ hasText: catalogEvaluation.evaluation_id }),
  ).toContainText('未提供')
  await expect(
    page
      .getByRole('row')
      .filter({ hasText: catalogEvaluation.evaluation_id })
      .locator('dd')
      .filter({ hasText: /^0$/ }),
  ).toHaveCount(1)
  await page.getByRole('button', { name: '下一页模型' }).click()
  await expect(page.getByRole('row').filter({ hasText: catalogModel.name })).toHaveCount(0)
  await expect(
    page.getByRole('row').filter({ hasText: catalogEvaluation.evaluation_id }),
  ).toBeVisible()
  expect(requests).toEqual([
    '/business/api/v1/models?limit=20',
    '/business/api/v1/models?limit=20&cursor=a%2Bb%2Fc%3D',
  ])
})

for (const status of [403, 503]) {
  test(`model page keeps ${status} refusal visible and clears the preceding page`, async ({
    page,
  }) => {
    await page.route('**/business/api/v1/models?**', (route) => {
      const cursor = new URL(route.request().url()).searchParams.has('cursor')
      return cursor
        ? route.fulfill({
            status,
            json: {
              code: status === 403 ? 'PERMISSION_REQUIRED' : 'CONDITIONAL_FACTS_UNAVAILABLE',
            },
          })
        : route.fulfill({ json: { items: [catalogModel], next_cursor: 'next-page' } })
    })
    await connectBusiness(page, ['model.read'])
    await page.getByRole('link', { name: '模型目录', exact: true }).click()
    await page.getByRole('button', { name: '查询模型／回到首页' }).click()
    await expect(page.getByRole('row').filter({ hasText: catalogModel.name })).toBeVisible()
    await page.getByRole('button', { name: '下一页模型' }).click()
    await expect(page.getByRole('status')).toContainText(
      status === 403 ? 'PERMISSION_REQUIRED' : 'CONDITIONAL_FACTS_UNAVAILABLE',
    )
    await expect(page.getByRole('row').filter({ hasText: catalogModel.name })).toHaveCount(0)
    await expect(page.getByRole('button', { name: '下一页模型' })).toBeDisabled()
  })
}

test('leaving model page and clearing identity discards a delayed directory response', async ({
  page,
}) => {
  let release!: () => void
  let started!: () => void
  let finished!: () => void
  const fulfilled = new Promise<void>((resolve) => {
    finished = resolve
  })
  const waiting = new Promise<void>((resolve) => {
    release = resolve
  })
  const requested = new Promise<void>((resolve) => {
    started = resolve
  })
  await page.route('**/business/api/v1/models?**', async (route) => {
    started()
    await waiting
    await route.fulfill({ json: { items: [catalogModel], next_cursor: 'old-cursor' } })
    finished()
  })
  await connectBusiness(page, ['model.read'])
  await page.getByRole('link', { name: '模型目录', exact: true }).click()
  await page.getByRole('button', { name: '查询模型／回到首页' }).click()
  await requested
  await page.getByRole('link', { name: '业务身份', exact: true }).click()
  const aborted = page.waitForEvent('requestfailed', {
    predicate: (request) => request.url().includes('/models?'),
  })
  await page.getByRole('button', { name: '清除身份与结果' }).click()
  expect((await aborted).failure()?.errorText).toBe('net::ERR_ABORTED')
  release()
  await fulfilled
  await page.getByRole('link', { name: '模型目录', exact: true }).click()
  await expect(page.getByRole('row').filter({ hasText: catalogModel.name })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '下一页模型' })).toBeDisabled()
})

test('health navigation shares the in-memory token and reload clears it', async ({ page }) => {
  await page.route('**/api/v1/health', (route) => route.fulfill({ json: { status: 'ok' } }))
  await page.goto('/#/')
  await page.getByLabel('研发访问令牌').fill('self-owned-browser-token')
  await page.getByRole('link', { name: '系统健康' }).click()
  await expect(page.getByRole('heading', { name: '系统健康' })).toBeVisible()
  await expect(page.getByLabel('研发访问令牌')).toHaveValue('self-owned-browser-token')
  await page.getByRole('button', { name: '检查状态' }).click()
  await expect(page.getByRole('status')).toContainText('服务可用')
  await page.reload()
  await expect(page.getByRole('heading', { name: '系统健康' })).toBeVisible()
  await expect(page.getByLabel('研发访问令牌')).toHaveValue('')
  await page.getByRole('link', { name: '上传验证' }).click()
  await expect(page.getByRole('heading', { name: '提交测试图片' })).toBeVisible()
})

test('health service failures remain visible as failures', async ({ page }) => {
  await page.route('**/api/v1/health', (route) =>
    route.fulfill({ status: 503, json: { code: 'DATABASE_UNAVAILABLE' } }),
  )
  await page.goto('/#/health')
  await page.getByRole('button', { name: '检查状态' }).click()
  await expect(page.getByRole('status')).toContainText('检查失败')
  await expect(page.getByRole('status')).not.toContainText('服务可用')
})

test('unknown routes have a usable return path', async ({ page }) => {
  await page.goto('/#/does-not-exist')
  await expect(page.getByRole('heading', { name: '页面不存在' })).toBeVisible()
  await page.getByRole('link', { name: '返回上传验证' }).click()
  await expect(page.getByRole('heading', { name: '提交测试图片' })).toBeVisible()
})

// Self-owned transport fixtures prove UI behavior, not real identity acceptance.
const taskId = '11111111-1111-4111-8111-111111111111'
const caseId = '22222222-2222-4222-8222-222222222222'
const otherCaseId = '33333333-3333-4333-8333-333333333333'
async function connectBusiness(
  page: Page,
  permissions = ['task.read', 'review.read', 'asset.read'],
  caseIds = [caseId, otherCaseId],
) {
  await page.route('**/business/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        user_id: '44444444-4444-4444-8444-444444444444',
        org_id: '55555555-5555-4555-8555-555555555555',
        roles: ['self-owned-browser-fixture'],
        permissions,
        case_ids: caseIds,
      },
    }),
  )
  await page.goto('/#/business')
  await page.getByLabel('业务访问令牌').fill('self-owned-business-browser-token')
  await page.getByRole('button', { name: '连接身份', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('业务身份已连接')
  await expect(page.getByLabel('业务访问令牌')).toHaveValue('')
}

function cancelExecution(state: Schemas['TaskExecutionStatus']['state'] = 'RUNNING') {
  return {
    task_id: taskId,
    case_id: caseId,
    state,
    run_version: 2,
    result_version: 0,
    version: 7,
    result_available: false,
  }
}

test('task cancellation requires a fresh condition and explicit confirmation, acceptance is not stopped', async ({
  page,
}) => {
  const mutations: { body: unknown; key: string | undefined; etag: string | undefined }[] = []
  let state: Schemas['TaskExecutionStatus']['state'] = 'RUNNING'
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/execution`, (route) =>
    route.fulfill({ json: cancelExecution(state), headers: { ETag: '"execution-7"' } }),
  )
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/cancel`, (route) => {
    mutations.push({
      body: route.request().postDataJSON(),
      key: route.request().headers()['idempotency-key'],
      etag: route.request().headers()['if-match'],
    })
    state = 'CANCEL_REQUESTED'
    return route.fulfill({
      status: 202,
      json: { task_id: taskId, state, status_url: `/api/v1/analysis/tasks/${taskId}/execution` },
    })
  })
  await connectBusiness(page, ['task.read', 'task.cancel'])
  await page.goto('/#/tasks')
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await expect(page.getByRole('button', { name: '提交取消申请', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await page.getByLabel('取消原因', { exact: true }).fill('browser-owned cancellation intent')
  await expect(page.getByRole('button', { name: '提交取消申请', exact: true })).toBeDisabled()
  await page.getByLabel('我确认提交取消申请，受理不代表已停止').check()
  await page.getByRole('button', { name: '提交取消申请', exact: true }).click()
  await expect(page.getByTestId('task-cancel-status')).toContainText('取消申请已受理，尚未确认停止')
  expect(mutations).toHaveLength(1)
  expect(mutations[0]?.etag).toBe('"execution-7"')
  expect(mutations[0]?.key).toBeTruthy()
  expect(mutations[0]?.body).toEqual({
    reason: 'browser-owned cancellation intent',
    approval_id: null,
    expected_run_version: 2,
    expected_version: 7,
  })
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await expect(page.getByTestId('task-cancel-status')).toContainText('CANCEL_REQUESTED')
  await expect(page.getByRole('button', { name: '提交取消申请', exact: true })).toBeDisabled()
})

test('task cancellation ambiguous failure retries the unchanged original request', async ({
  page,
}) => {
  const requests: { body: string | null; key: string | undefined; etag: string | undefined }[] = []
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/execution`, (route) =>
    route.fulfill({ json: cancelExecution(), headers: { ETag: '"execution-7"' } }),
  )
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/cancel`, (route) => {
    requests.push({
      body: route.request().postData(),
      key: route.request().headers()['idempotency-key'],
      etag: route.request().headers()['if-match'],
    })
    return requests.length === 1
      ? route.fulfill({
          status: 500,
          json: { code: 'INTERNAL_ERROR', detail: 'do not show private text' },
        })
      : route.fulfill({
          status: 202,
          json: {
            task_id: taskId,
            state: 'CANCEL_REQUESTED',
            status_url: `/api/v1/analysis/tasks/${taskId}/execution`,
          },
        })
  })
  await connectBusiness(page, ['task.read', 'task.cancel'])
  await page.goto('/#/tasks')
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await page.getByLabel('取消原因', { exact: true }).fill('original intent')
  await page.getByLabel('我确认提交取消申请，受理不代表已停止').check()
  await page.getByRole('button', { name: '提交取消申请', exact: true }).click()
  await expect(page.getByTestId('task-cancel-status')).toContainText('结果未确认')
  await expect(page.getByLabel('取消原因', { exact: true })).toBeDisabled()
  await expect(page.getByRole('button', { name: '读取取消条件', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: '重试原取消申请', exact: true }).click()
  await expect(page.getByTestId('task-cancel-status')).toContainText('尚未确认停止')
  expect(requests).toHaveLength(2)
  expect(requests[0]).toEqual(requests[1])
  await expect(page.getByTestId('task-cancel-status')).not.toContainText('private text')
})

test('task cancellation denied permission or a changed task clears controls', async ({ page }) => {
  let reads = 0
  await page.route('**/business/api/v1/analysis/tasks/**/execution', (route) => {
    reads++
    return route.fulfill({ json: cancelExecution(), headers: { ETag: '"execution-7"' } })
  })
  await connectBusiness(page, ['task.read'])
  await page.goto('/#/tasks')
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await expect(page.getByRole('button', { name: '读取取消条件', exact: true })).toBeDisabled()
  expect(reads).toBe(0)
  await connectBusiness(page, ['task.read', 'task.cancel'])
  await page.goto('/#/tasks')
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await page.getByLabel('取消原因', { exact: true }).fill('old task reason')
  await page.getByLabel('任务编号', { exact: true }).fill(otherCaseId)
  await expect(page.getByLabel('取消原因', { exact: true })).toHaveValue('')
  await expect(page.getByRole('button', { name: '提交取消申请', exact: true })).toBeDisabled()
})

test('task cancellation version refusal requires another explicit confirmation after fresh read', async ({
  page,
}) => {
  let version = 7
  const sent: number[] = []
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/execution`, (route) =>
    route.fulfill({
      json: { ...cancelExecution(), version },
      headers: { ETag: `"execution-${version}"` },
    }),
  )
  await page.route(`**/business/api/v1/analysis/tasks/${taskId}/cancel`, (route) => {
    sent.push(route.request().postDataJSON().expected_version)
    if (sent.length === 1) {
      version = 8
      return route.fulfill({ status: 412, json: { code: 'PRECONDITION_FAILED' } })
    }
    return route.fulfill({
      status: 202,
      json: {
        task_id: taskId,
        state: 'CANCEL_REQUESTED',
        status_url: `/api/v1/analysis/tasks/${taskId}/execution`,
      },
    })
  })
  await connectBusiness(page, ['task.read', 'task.cancel'])
  await page.goto('/#/tasks')
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await page.getByLabel('取消原因', { exact: true }).fill('freshly confirmed browser intent')
  await page.getByLabel('我确认提交取消申请，受理不代表已停止').check()
  await page.getByRole('button', { name: '提交取消申请', exact: true }).click()
  await expect(page.getByRole('button', { name: '读取取消条件', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '读取取消条件', exact: true }).click()
  await expect(page.getByLabel('取消原因', { exact: true })).toBeEnabled()
  await expect(page.getByRole('button', { name: '提交取消申请', exact: true })).toBeDisabled()
  await page.getByLabel('我确认提交取消申请，受理不代表已停止').check()
  await page.getByRole('button', { name: '提交取消申请', exact: true }).click()
  await expect(page.getByTestId('task-cancel-status')).toContainText('取消申请已受理，尚未确认停止')
  expect(sent).toEqual([7, 8])
  if (process.env.MT_TASK_CANCEL_SCREENSHOT)
    await page.screenshot({ path: process.env.MT_TASK_CANCEL_SCREENSHOT, fullPage: true })
})

const sourceId = '70000000-0000-4000-8000-000000000001'
function registeredSource(selectedCase = caseId): Schemas['Source'] {
  return {
    source_id: sourceId,
    case_id: selectedCase,
    name: 'browser-owned source',
    source_type: 'public_licensed',
    authorization_ref: 'javascript:alert(1)',
    purpose: ['analysis', 'download'],
    expires_at: null,
    authorization_status: 'pending',
    version: 1,
  }
}

test('source console requires identity and separates source read from manage', async ({ page }) => {
  let requests = 0
  await page.route('**/business/api/v1/sources**', (route) => {
    requests++
    return route.fulfill({ json: { items: [], next_cursor: null } })
  })
  await page.goto('/#/sources')
  await expect(page.getByRole('button', { name: '查询来源／回到首页' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '登记来源', exact: true })).toBeDisabled()
  await connectBusiness(page, ['source.read'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await expect(page.getByRole('button', { name: '查询来源／回到首页' })).toBeEnabled()
  await expect(page.getByRole('button', { name: '登记来源', exact: true })).toBeDisabled()
  expect(requests).toBe(0)
})

test('source console reads case-scoped metadata and preserves opaque pagination', async ({
  page,
}) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/sources?**', (route) => {
    const url = new URL(route.request().url())
    requests.push(url.pathname + url.search)
    return route.fulfill({
      json: {
        items: url.searchParams.has('cursor') ? [] : [registeredSource()],
        next_cursor: url.searchParams.has('cursor') ? null : 'a+b/c=',
      },
    })
  })
  await page.route(`**/business/api/v1/sources/${sourceId}`, (route) =>
    route.fulfill({ json: registeredSource() }),
  )
  await connectBusiness(page, ['source.read'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询来源／回到首页' }).click()
  await expect(page.getByRole('row').filter({ hasText: sourceId })).toContainText('pending')
  await page.getByRole('button', { name: '查看来源详情' }).click()
  await expect(page.getByText('javascript:alert(1)', { exact: true }).first()).toBeVisible()
  await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0)
  await page.getByRole('button', { name: '下一页来源' }).click()
  expect(requests).toEqual([
    `/business/api/v1/sources?case_id=${caseId}&limit=20`,
    `/business/api/v1/sources?case_id=${caseId}&limit=20&cursor=a%2Bb%2Fc%3D`,
  ])
  await expect(page.getByRole('row').filter({ hasText: sourceId })).toHaveCount(0)
})

test('source registration keeps a refused original request for exact idempotent retry', async ({
  page,
}) => {
  const writes: { key: string | undefined; body: Schemas['SourceCreate'] }[] = []
  await page.route('**/business/api/v1/sources', (route) => {
    const request = route.request()
    writes.push({ key: request.headers()['idempotency-key'], body: request.postDataJSON() })
    if (writes.length === 1)
      return route.fulfill({ status: 503, json: { code: 'SOURCE_SYNCHRONIZATION_UNAVAILABLE' } })
    return route.fulfill({ status: 201, json: { ...registeredSource(), ...writes[0]!.body } })
  })
  await connectBusiness(page, ['source.manage'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByLabel('来源名称', { exact: true }).fill('browser-owned source')
  await page.getByLabel('来源类型', { exact: true }).selectOption('public_licensed')
  await page.getByLabel('授权依据', { exact: true }).fill('license-record/1')
  await page.getByLabel('用途（每行一项）', { exact: true }).fill('analysis\ndownload')
  await page.getByRole('button', { name: '登记来源', exact: true }).click()
  await expect(
    page.getByRole('status').filter({ hasText: 'SOURCE_SYNCHRONIZATION_UNAVAILABLE' }),
  ).toBeVisible()
  await expect(page.getByText(sourceId, { exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: '重试原登记请求', exact: true }).click()
  await expect(page.getByText(sourceId, { exact: true }).first()).toBeVisible()
  await expect(page.getByText(/^pending\s*／\s*1$/)).toBeVisible()
  await expect(page.getByText('verified', { exact: true })).toHaveCount(0)
  expect(writes).toHaveLength(2)
  expect(writes[0]!.key).toBeTruthy()
  expect(writes[0]!.key!.length).toBeLessThanOrEqual(128)
  expect(writes[1]).toEqual(writes[0])
  expect(Object.keys(writes[0]!.body).sort()).toEqual([
    'authorization_ref',
    'case_id',
    'expires_at',
    'name',
    'purpose',
    'source_type',
  ])
  expect(writes[0]!.body).toEqual({
    case_id: caseId,
    name: 'browser-owned source',
    source_type: 'public_licensed',
    authorization_ref: 'license-record/1',
    purpose: ['analysis', 'download'],
    expires_at: null,
  })
})

test('source console clears preceding case records immediately on case selection change', async ({
  page,
}) => {
  await page.route('**/business/api/v1/sources?**', (route) =>
    route.fulfill({ json: { items: [registeredSource()], next_cursor: 'old-case-cursor' } }),
  )
  await connectBusiness(page, ['source.read'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询来源／回到首页' }).click()
  await expect(page.getByRole('row').filter({ hasText: sourceId })).toBeVisible()
  await page.getByLabel('来源案件编号').fill(otherCaseId)
  await expect(page.getByRole('row').filter({ hasText: sourceId })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '下一页来源' })).toBeDisabled()
})

test('source console clears registration drafts when manage permission changes without reconnect', async ({
  page,
}) => {
  await connectBusiness(page, ['source.read', 'source.manage'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByLabel('来源名称', { exact: true }).fill('private draft in self-owned fixture')
  await page.getByLabel('授权依据', { exact: true }).fill('self-owned-unsubmitted-authorization')
  await page.getByLabel('用途（每行一项）', { exact: true }).fill('analysis')
  // A self-owned reactive-session mutation, not a server-side ACL or real revocation test.
  await page.evaluate(() => {
    const root = document.getElementById('app') as HTMLElement & {
      _vnode?: { component?: { provides: Record<symbol, unknown> } }
    }
    const provides = root?._vnode?.component?.provides
    const key =
      provides &&
      Object.getOwnPropertySymbols(provides).find((item) => item.description === 'business-session')
    if (!provides || !key) throw new Error('SELF_OWNED_SESSION_FIXTURE_MISSING')
    const session = provides[key] as { state: { user: { permissions: string[] } } }
    session.state.user.permissions = ['source.read']
  })
  await expect(page.getByLabel('来源名称', { exact: true })).toHaveValue('')
  await expect(page.getByLabel('授权依据', { exact: true })).toHaveValue('')
  await expect(page.getByLabel('用途（每行一项）', { exact: true })).toHaveValue('')
  await expect(page.getByRole('button', { name: '登记来源', exact: true })).toBeDisabled()
})

test('source synchronization binds the service ETag and keeps revoked receipt separate from fresh detail', async ({
  page,
}) => {
  const requests: {
    method: string
    body: Schemas['SourceSyncRequest']
    key: string | undefined
    etag: string | undefined
  }[] = []
  let detailReads = 0
  await page.route('**/business/api/v1/sources?**', (route) =>
    route.fulfill({ json: { items: [registeredSource()], next_cursor: null } }),
  )
  await page.route(`**/business/api/v1/sources/${sourceId}`, (route) => {
    detailReads++
    return route.fulfill({
      headers: {
        ETag: detailReads === 1 ? '"source-browser-original"' : '"source-browser-current"',
      },
      json:
        detailReads === 1
          ? registeredSource()
          : { ...registeredSource(), version: 3, authorization_status: 'verified' },
    })
  })
  await page.route(`**/business/api/v1/sources/${sourceId}/authorization/sync`, (route) => {
    const request = route.request()
    requests.push({
      method: request.method(),
      body: request.postDataJSON(),
      key: request.headers()['idempotency-key'],
      etag: request.headers()['if-match'],
    })
    return route.fulfill({
      headers: { ETag: '"source-browser-sync-receipt"' },
      json: { ...registeredSource(), version: 2, authorization_status: 'revoked' },
    })
  })
  await connectBusiness(page, ['source.read', 'source.manage'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询来源／回到首页' }).click()
  await page.getByRole('button', { name: '查看来源详情' }).click()
  await page.getByRole('button', { name: '同步来源授权', exact: true }).click()
  const receipt = page.locator('dl.source-detail').filter({ hasText: '同步回执来源编号' })
  await expect(receipt).toContainText('revoked／2')
  await expect(
    page.getByText('当前详情已清空，请点击“重新读取来源详情”查看当前状态。', { exact: true }),
  ).toBeVisible()
  await expect(page.getByRole('button', { name: '同步来源授权', exact: true })).toBeDisabled()
  expect(detailReads).toBe(1)
  expect(requests).toHaveLength(1)
  expect(requests[0]).toMatchObject({
    method: 'POST',
    body: { expected_version: 1 },
    etag: '"source-browser-original"',
  })
  expect(requests[0]!.body).toEqual({ expected_version: 1 })
  expect(requests[0]!.key).toMatch(/^[0-9a-f-]{36}$/)
  await page.getByRole('button', { name: '重新读取来源详情', exact: true }).click()
  const current = page.locator('dl.source-detail').filter({ hasText: '记录版本' })
  await expect(current).toContainText('verified')
  await expect(current).not.toContainText('revoked')
  await expect(current.locator('dd').last()).toHaveText('3')
  await expect(receipt).toContainText('revoked／2')
  expect(detailReads).toBe(2)
  expect(requests).toHaveLength(1)
})

test('source synchronization unknown result keeps original request after new detail and repeated conflicts', async ({
  page,
}) => {
  const requests: {
    body: Schemas['SourceSyncRequest']
    key: string | undefined
    etag: string | undefined
  }[] = []
  let detailReads = 0
  await page.route('**/business/api/v1/sources?**', (route) =>
    route.fulfill({ json: { items: [registeredSource()], next_cursor: null } }),
  )
  await page.route(`**/business/api/v1/sources/${sourceId}`, (route) => {
    detailReads++
    return route.fulfill({
      headers: { ETag: detailReads === 1 ? '"source-browser-original"' : '"source-browser-newer"' },
      json: { ...registeredSource(), version: detailReads === 1 ? 1 : 7 },
    })
  })
  await page.route(`**/business/api/v1/sources/${sourceId}/authorization/sync`, (route) => {
    const request = route.request()
    requests.push({
      body: request.postDataJSON(),
      key: request.headers()['idempotency-key'],
      etag: request.headers()['if-match'],
    })
    return route.fulfill({
      status: requests.length === 1 ? 503 : 409,
      json: {
        code: requests.length === 1 ? 'SOURCE_SYNCHRONIZATION_UNAVAILABLE' : 'VERSION_CONFLICT',
      },
    })
  })
  await connectBusiness(page, ['source.read', 'source.manage'])
  await page.getByRole('link', { name: '来源管理', exact: true }).click()
  await page.getByLabel('来源案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询来源／回到首页' }).click()
  await page.getByRole('button', { name: '查看来源详情' }).click()
  await page.getByRole('button', { name: '同步来源授权', exact: true }).click()
  await expect(page.getByText(/SOURCE_SYNCHRONIZATION_UNAVAILABLE/)).toBeVisible()
  await expect(page.getByRole('button', { name: '重试原授权同步请求', exact: true })).toBeVisible()
  await page.getByRole('button', { name: '重新读取来源详情', exact: true }).click()
  await expect(
    page.locator('dl.source-detail').filter({ hasText: '记录版本' }).locator('dd').last(),
  ).toHaveText('7')
  await expect(page.getByRole('button', { name: '同步来源授权', exact: true })).toBeDisabled()
  expect(requests).toHaveLength(1)
  const retry = page.getByRole('button', { name: '重试原授权同步请求', exact: true })
  await retry.click()
  await expect(page.getByText(/VERSION_CONFLICT/)).toBeVisible()
  await expect(retry).toBeEnabled()
  expect(requests).toHaveLength(2)
  expect(requests[0]!.key).toMatch(/^[0-9a-f-]{36}$/)
  expect(requests[0]).toMatchObject({
    body: { expected_version: 1 },
    etag: '"source-browser-original"',
  })
  expect(requests[0]!.body).toEqual({ expected_version: 1 })
  expect(requests[1]).toEqual(requests[0])
  await retry.click()
  await expect.poll(() => requests.length).toBe(3)
  await expect(retry).toBeEnabled()
  expect(requests[2]).toEqual(requests[0])
  await expect(
    page.locator('dl.source-detail').filter({ hasText: '同步回执来源编号' }),
  ).toHaveCount(0)
  await expect(page.getByRole('button', { name: '同步来源授权', exact: true })).toBeDisabled()
})

test('business reading pages require a connected identity', async ({ page }) => {
  await page.goto('/#/tasks')
  await expect(page.getByRole('heading', { name: '任务与结果', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '查询任务状态' })).toBeDisabled()
  await page.getByRole('link', { name: '审核管理（待复核队列）', exact: true }).click()
  await expect(page.getByRole('heading', { name: '待复核队列', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '查询待复核' })).toBeDisabled()
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await expect(page.getByRole('heading', { name: '媒体资产库', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '查询资产／回到首页' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '读取资产详情' })).toBeDisabled()
})

test('task monitor reads live execution without inventing a result snapshot', async ({ page }) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/analysis/tasks/**', (route) => {
    const url = new URL(route.request().url())
    requests.push(url.pathname + url.search)
    if (url.pathname.endsWith('/execution'))
      return route.fulfill({
        headers: { ETag: '"1"' },
        json: {
          task_id: taskId,
          case_id: caseId,
          state: 'RUNNING',
          run_version: 2,
          result_version: 1,
          version: 1,
          result_available: false,
        },
      })
    if (url.pathname.endsWith('/nodes'))
      return route.fulfill({ json: { task_id: taskId, run_version: 2, items: [] } })
    return route.fulfill({ json: { items: [], next_cursor: null } })
  })
  await connectBusiness(page)
  await page.getByRole('link', { name: '任务与结果', exact: true }).click()
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await page.getByRole('button', { name: '查询任务状态' }).click()
  await expect(page.getByText('RUNNING', { exact: true })).toBeVisible()
  expect(requests).toHaveLength(3)
  expect(requests.some((url) => url.endsWith('/nodes?run_version=2'))).toBe(true)
  expect(requests.some((url) => url.includes('/events?run_version=2&limit=20'))).toBe(true)
  expect(requests.some((url) => url.includes('history'))).toBe(false)
  await page.getByLabel('任务编号', { exact: true }).fill('66666666-6666-4666-8666-666666666666')
  await expect(page.getByText('RUNNING', { exact: true })).toHaveCount(0)
})

test('pending review source blocks remain visible and case changes clear rows', async ({
  page,
}) => {
  await page.route('**/business/api/v1/reviews/pending?**', (route) =>
    route.fulfill({
      json: {
        items: [
          {
            task_id: taskId,
            case_id: caseId,
            task_state: 'WAIT_REVIEW',
            availability: 'SOURCE_BLOCKED',
            context: null,
          },
        ],
        next_cursor: null,
      },
    }),
  )
  await connectBusiness(page)
  await page.getByRole('link', { name: '审核管理（待复核队列）', exact: true }).click()
  await page.getByLabel('队列案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询待复核' }).click()
  await expect(page.getByRole('row').filter({ hasText: taskId })).toContainText(
    /SOURCE_BLOCKED|来源受阻/,
  )
  await page.getByLabel('队列案件编号').fill(otherCaseId)
  await expect(page.getByRole('row').filter({ hasText: taskId })).toHaveCount(0)
  await page.getByRole('button', { name: '查询待复核' }).click()
  await expect(page.getByRole('status')).toContainText('队列响应与查询案件不匹配')
  await expect(page.getByRole('row').filter({ hasText: taskId })).toHaveCount(0)
})

test('slow node reads do not replace an explicitly edited history selection', async ({ page }) => {
  let releaseNodes!: () => void
  const nodesReady = new Promise<void>((resolve) => {
    releaseNodes = resolve
  })
  await page.route('**/business/api/v1/analysis/tasks/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (path.endsWith('/execution'))
      return route.fulfill({
        json: {
          task_id: taskId,
          case_id: caseId,
          state: 'RUNNING',
          run_version: 2,
          result_version: 1,
          version: 1,
          result_available: false,
        },
      })
    if (path.endsWith('/nodes')) {
      await nodesReady
      return route.fulfill({ json: { task_id: taskId, run_version: 2, items: [] } })
    }
    return route.fulfill({ json: { items: [], next_cursor: null } })
  })
  await connectBusiness(page)
  await page.getByRole('link', { name: '任务与结果', exact: true }).click()
  await page.getByLabel('任务编号', { exact: true }).fill(taskId)
  await page.getByRole('button', { name: '查询任务状态' }).click()
  await expect(page.getByText('RUNNING', { exact: true })).toBeVisible()
  await page.getByLabel('历史运行版本').fill('7')
  await page.getByLabel('历史结果版本').fill('3')
  releaseNodes()
  await expect(page.getByText('此运行尚无节点记录。')).toBeVisible()
  await expect(page.getByLabel('历史运行版本')).toHaveValue('7')
  await expect(page.getByLabel('历史结果版本')).toHaveValue('3')
})

test('PPT desktop shell keeps real routes usable and marks unavailable modules', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/#/')
  await expect(
    page.getByRole('heading', { name: '短视频与图片智能识别溯源系统', exact: true }),
  ).toBeVisible()
  await expect(page.locator('.app-sidebar')).toBeVisible()
  await expect(
    page.getByRole('button', { name: '媒体预处理 暂未接入', exact: true }),
  ).toBeDisabled()
  await expect(page.getByText('业务身份未连接', { exact: true })).toBeVisible()
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await expect(page.getByRole('heading', { name: '媒体资产库', exact: true })).toBeVisible()
  await expect(
    page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }),
  ).toHaveAttribute('aria-current', 'page')
  await page.getByRole('link', { name: '任务与结果', exact: true }).click()
  await expect(page.getByRole('link', { name: '任务与结果', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  )
  await expect(page.getByRole('heading', { name: '任务与结果', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '查询任务状态' })).toBeDisabled()
  const sidebar = await page.locator('.app-sidebar').boundingBox()
  const workspace = await page.locator('#workspace-main').boundingBox()
  expect(sidebar && workspace && workspace.x >= sidebar.x + sidebar.width).toBeTruthy()
})

test('PPT mobile navigation opens closes and keeps forms inside the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/#/')
  await expect(page.getByRole('link', { name: '业务身份未连接', exact: true })).toBeVisible()
  await expect(page.locator('.app-sidebar')).toBeHidden()
  await page.getByRole('button', { name: '展开功能导航' }).click()
  await expect(page.locator('.app-sidebar')).toBeVisible()
  await page.getByRole('link', { name: '系统运维（系统健康）', exact: true }).click()
  await expect(page.getByRole('heading', { name: '系统健康', exact: true })).toBeVisible()
  await expect(page.locator('.app-sidebar')).toBeHidden()
  await expect(page.getByRole('button', { name: '展开功能导航' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})

test('PPT skip link focuses main content without changing the hash route', async ({ page }) => {
  await page.goto('/#/tasks')
  await page.getByRole('link', { name: '跳转到主要内容' }).focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#\/tasks$/)
  await expect(page.locator('#workspace-main')).toBeFocused()
  await expect(page.getByRole('heading', { name: '任务与结果', exact: true })).toBeVisible()
})

const assetId = '66666666-6666-4666-8666-666666666666'
const otherAssetId = '77777777-7777-4777-8777-777777777777'
function catalogAsset(id = assetId, selectedCase = caseId): Schemas['Asset'] {
  return {
    asset_id: id,
    case_id: selectedCase,
    content_id: '88888888-8888-4888-8888-888888888888',
    source_id: '99999999-9999-4999-8999-999999999999',
    kind: 'original',
    object_ref: { object_id: id, version_id: 'self-owned-fixed-v3', sha256: 'b'.repeat(64) },
    mime: 'image/png',
    size_bytes: 128,
    duration_ms: null,
    width: 24,
    height: 16,
    state: 'VALID',
    version: 3,
    created_at: '2026-10-21T00:00:00Z',
  }
}
function catalogTask(id = taskId, selectedCase = caseId): Schemas['Task'] {
  return {
    task_id: id,
    case_id: selectedCase,
    asset_id: assetId,
    state: 'QUEUED',
    run_version: 2,
    result_version: 0,
    policy_version: 'self-owned-policy',
    version: 3,
    progress: 0,
    nodes: [
      {
        node_code: 'MEDIA',
        state: 'DEFERRED',
        attempt: 2,
        reason: 'RESOURCE_LIMIT',
        required: true,
      },
    ],
    missing_modalities: ['audio'],
    report_eligibility: 'draft_only',
    created_at: '2026-10-21T00:00:00Z',
  }
}

test('asset transport fixture supports scoped paging, current-page filters and read-only fixed object detail', async ({
  page,
}) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/assets?**', (route) => {
    const url = new URL(route.request().url())
    requests.push(url.pathname + url.search)
    expect(route.request().method()).toBe('GET')
    expect(route.request().headers().authorization).toBe('Bearer self-owned-business-browser-token')
    const item = catalogAsset(
      url.searchParams.has('cursor') ? otherAssetId : assetId,
      url.searchParams.get('case_id')!,
    )
    if (url.searchParams.has('cursor')) {
      item.kind = 'derived'
      item.state = 'QUARANTINED'
    }
    return route.fulfill({
      json: { items: [item], next_cursor: url.searchParams.has('cursor') ? null : 'a+b/c=' },
    })
  })
  await page.route(`**/business/api/v1/assets/${assetId}`, (route) =>
    route.fulfill({ json: catalogAsset() }),
  )
  await connectBusiness(page)
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await page.getByRole('button', { name: '查询资产／回到首页' }).click()
  await expect(page.getByRole('status').filter({ hasText: '完整对象编号' })).toBeVisible()
  expect(requests).toHaveLength(0)
  await page.getByLabel('资产案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询资产／回到首页' }).click()
  await expect(page.getByRole('row').filter({ hasText: assetId })).toContainText('VALID')
  await page.getByRole('button', { name: '查看详情', exact: true }).click()
  await expect(page.locator('dd').filter({ hasText: 'self-owned-fixed-v3' })).toBeVisible()
  await expect(page.locator('dd').filter({ hasText: 'b'.repeat(64) })).toBeVisible()
  await expect(page.getByText('完整血缘尚未接入本页', { exact: false })).toBeVisible()
  await expect(page.getByRole('region', { name: '资产来源授权', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '读取来源授权明细', exact: true })).toBeDisabled()
  await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toBeDisabled()
  await expect(page.locator('dl input, dl textarea, dl button')).toHaveCount(0)
  await page.getByRole('button', { name: '下一页资产' }).click()
  await expect(page.getByRole('row').filter({ hasText: otherAssetId })).toContainText('QUARANTINED')
  await expect(page.locator('dd')).toHaveCount(0)
  expect(requests[1]).toBe(`/business/api/v1/assets?case_id=${caseId}&limit=20&cursor=a%2Bb%2Fc%3D`)
  await page.getByLabel('资产当前页状态').selectOption('VALID')
  await expect(page.getByText('当前页没有符合条件的可见资产', { exact: false })).toBeVisible()
  await page.getByLabel('资产当前页状态').selectOption('')
  await page.getByLabel('资产案件编号').fill(otherCaseId)
  await expect(page.getByRole('row').filter({ hasText: otherAssetId })).toHaveCount(0)
  await page.getByLabel('资产每页条数').selectOption('10')
  await page.getByRole('button', { name: '查询资产／回到首页' }).click()
  await expect(page.getByRole('row').filter({ hasText: assetId })).toBeVisible()
  expect(requests[2]).toBe(`/business/api/v1/assets?case_id=${otherCaseId}&limit=10`)
})

test('task transport fixture lists zero-result tasks and opens current execution without invented DAG progress', async ({
  page,
}) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/analysis/tasks?**', (route) => {
    requests.push(route.request().url())
    return route.fulfill({ json: { items: [catalogTask()], next_cursor: null } })
  })
  await page.route('**/business/api/v1/analysis/tasks/**', (route) => {
    const path = new URL(route.request().url()).pathname
    requests.push(path)
    if (path.endsWith('/execution'))
      return route.fulfill({
        json: {
          task_id: taskId,
          case_id: caseId,
          state: 'QUEUED',
          run_version: 2,
          result_version: 0,
          version: 3,
          result_available: false,
        },
      })
    if (path.endsWith('/nodes'))
      return route.fulfill({ json: { task_id: taskId, run_version: 2, items: [] } })
    return route.fulfill({ json: { items: [], next_cursor: null } })
  })
  await connectBusiness(page)
  await page.getByRole('link', { name: '任务与结果', exact: true }).click()
  await page.getByLabel('任务列表案件编号').fill(caseId)
  await page.getByRole('button', { name: '查询任务／回到首页' }).click()
  const row = page.getByRole('row').filter({ hasText: taskId })
  await expect(row).toContainText('QUEUED')
  await expect(row).toContainText('尚无结果版本')
  await expect(row).toContainText('DEFERRED')
  await expect(row).toContainText('RESOURCE_LIMIT')
  await expect(page.getByText('真实DAG进度计算尚待验证', { exact: false })).toBeVisible()
  await row.getByRole('button', { name: '查看任务', exact: true }).click()
  await expect(page.getByLabel('任务编号', { exact: true })).toHaveValue(taskId)
  await expect(page.getByText('结果不可用；当前执行状态仍可观察')).toBeVisible()
  await expect(page.getByLabel('历史运行版本')).toHaveValue('2')
  await expect(page.getByLabel('历史结果版本')).toHaveValue('')
  expect(requests).toHaveLength(4)
  expect(requests.some((url) => url.includes('history'))).toBe(false)
  await page.getByLabel('任务列表案件编号').fill(otherCaseId)
  await expect(row).toHaveCount(0)
  await expect(page.getByLabel('任务编号', { exact: true })).toHaveValue('')
  await expect(page.getByText('结果不可用；当前执行状态仍可观察')).toHaveCount(0)
})

const catalogPages = [
  {
    name: 'assets',
    path: 'assets',
    link: '资源库（媒体资产管理）',
    label: '资产案件编号',
    query: '查询资产／回到首页',
    item: catalogAsset,
  },
  {
    name: 'tasks',
    path: 'analysis/tasks',
    link: '任务与结果',
    label: '任务列表案件编号',
    query: '查询任务／回到首页',
    item: catalogTask,
  },
]
for (const catalogPage of catalogPages) {
  test(`${catalogPage.name} transport fixture rejects cross-case rows`, async ({ page }) => {
    await page.route(`**/business/api/v1/${catalogPage.path}?**`, (route) =>
      route.fulfill({
        json: { items: [catalogPage.item(undefined, otherCaseId)], next_cursor: null },
      }),
    )
    await connectBusiness(page)
    await page.getByRole('link', { name: catalogPage.link, exact: true }).click()
    await page.getByLabel(catalogPage.label).fill(caseId)
    await page.getByRole('button', { name: catalogPage.query }).click()
    await expect(
      page.getByRole('status').filter({ hasText: '列表响应与查询案件不匹配' }),
    ).toBeVisible()
    await expect(page.locator('tbody tr')).toHaveCount(0)
  })

  test(`${catalogPage.name} transport fixture discards a late response after changing case`, async ({
    page,
  }) => {
    let release!: () => void
    const ready = new Promise<void>((resolve) => {
      release = resolve
    })
    let started!: () => void
    const observed = new Promise<void>((resolve) => {
      started = resolve
    })
    let completed!: () => void
    const returned = new Promise<void>((resolve) => {
      completed = resolve
    })
    await page.route(`**/business/api/v1/${catalogPage.path}?**`, async (route) => {
      const selectedCase = new URL(route.request().url()).searchParams.get('case_id')!
      if (selectedCase === caseId) {
        started()
        await ready
        await route.fulfill({ json: { items: [catalogPage.item()], next_cursor: 'stale-cursor' } })
        completed()
      } else
        await route.fulfill({
          json: { items: [catalogPage.item(otherAssetId, selectedCase)], next_cursor: null },
        })
    })
    await connectBusiness(page)
    await page.getByRole('link', { name: catalogPage.link, exact: true }).click()
    await page.getByLabel(catalogPage.label).fill(caseId)
    await page.getByRole('button', { name: catalogPage.query }).click()
    await observed
    await page.getByLabel(catalogPage.label).fill(otherCaseId)
    await page.getByRole('button', { name: catalogPage.query }).click()
    await expect(page.getByRole('row').filter({ hasText: otherAssetId })).toBeVisible()
    release()
    await returned
    await expect(
      page.getByRole('row').filter({ hasText: catalogPage.name === 'assets' ? assetId : taskId }),
    ).toHaveCount(0)
    await expect(page.getByRole('row').filter({ hasText: otherAssetId })).toBeVisible()
    await expect(
      page.getByRole('button', {
        name: catalogPage.name === 'assets' ? '下一页资产' : '下一页任务',
      }),
    ).toBeDisabled()
  })
}

for (const catalogPage of catalogPages)
  for (const status of [401, 403, 404, 503]) {
    test(`${catalogPage.name} transport fixture HTTP ${status} clears prior data and preserves failure state`, async ({
      page,
    }) => {
      let fail = false
      await page.route(`**/business/api/v1/${catalogPage.path}?**`, (route) =>
        fail
          ? route.fulfill({ status, json: { code: 'CATALOG_UNAVAILABLE' } })
          : route.fulfill({ json: { items: [catalogPage.item()], next_cursor: null } }),
      )
      await connectBusiness(page)
      await page.getByRole('link', { name: catalogPage.link, exact: true }).click()
      await page.getByLabel(catalogPage.label).fill(caseId)
      await page.getByRole('button', { name: catalogPage.query }).click()
      await expect(
        page.getByRole('row').filter({ hasText: catalogPage.name === 'assets' ? assetId : taskId }),
      ).toBeVisible()
      fail = true
      await page.getByRole('button', { name: catalogPage.query }).click()
      await expect(page.locator('tbody tr')).toHaveCount(0)
      if (status === 401) {
        await expect(page.getByRole('link', { name: '业务身份未连接', exact: true })).toBeVisible()
        await expect(page.getByRole('button', { name: catalogPage.query })).toBeDisabled()
        const catalogPanel = page.locator('section').filter({
          has: page.getByRole('heading', {
            name: catalogPage.name === 'assets' ? '媒体资产库' : '案件任务列表',
            exact: true,
          }),
        })
        await expect(catalogPanel.getByRole('status')).toContainText('请先在业务身份页连接身份。')
      } else
        await expect(
          page.getByRole('status').filter({ hasText: 'CATALOG_UNAVAILABLE' }),
        ).toBeVisible()
      await expect(
        page.getByText(
          catalogPage.name === 'assets'
            ? '当前页没有符合条件的可见资产'
            : '当前页没有符合条件的可见任务',
          { exact: false },
        ),
      ).toHaveCount(0)
    })
  }

test('asset detail transport fixture rejects a different case and discards an older object response', async ({
  page,
}) => {
  let mode = 'wrong-case'
  let release!: () => void
  const ready = new Promise<void>((resolve) => {
    release = resolve
  })
  let started!: () => void
  const observed = new Promise<void>((resolve) => {
    started = resolve
  })
  await page.route('**/business/api/v1/assets/*', async (route) => {
    const id = new URL(route.request().url()).pathname.split('/').at(-1)!
    if (id === otherAssetId) {
      const item = catalogAsset(otherAssetId)
      item.object_ref.version_id = 'self-owned-new-selection'
      return route.fulfill({ json: item })
    }
    if (mode === 'wrong-case') return route.fulfill({ json: catalogAsset(assetId, otherCaseId) })
    started()
    await ready
    return route.fulfill({ json: catalogAsset() })
  })
  await connectBusiness(page)
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await page.getByLabel('资产案件编号').fill(caseId)
  await page.getByLabel('资产详情编号').fill(assetId)
  await page.getByRole('button', { name: '读取资产详情' }).click()
  await expect(
    page.getByRole('status').filter({ hasText: '资产详情与所选案件或对象不匹配' }),
  ).toBeVisible()
  await expect(page.locator('dd')).toHaveCount(0)
  mode = 'pending'
  await page.getByRole('button', { name: '读取资产详情' }).click()
  await observed
  await page.getByLabel('资产详情编号').fill(otherAssetId)
  await page.getByRole('button', { name: '读取资产详情' }).click()
  await expect(page.locator('dd').filter({ hasText: 'self-owned-new-selection' })).toBeVisible()
  const response = page.waitForResponse((reply) =>
    new URL(reply.url()).pathname.endsWith(`/assets/${assetId}`),
  )
  release()
  await response
  await expect(page.locator('dd').filter({ hasText: 'self-owned-fixed-v3' })).toHaveCount(0)
  await expect(page.locator('dd').filter({ hasText: 'self-owned-new-selection' })).toBeVisible()
})

async function openDownloadAsset(page: Page) {
  const body = Buffer.from('self-owned browser download bytes')
  const item = catalogAsset()
  item.size_bytes = body.length
  item.object_ref.sha256 = createHash('sha256').update(body).digest('hex')
  const etag =
    '"' +
    createHash('sha256')
      .update(
        JSON.stringify([
          item.object_ref.object_id,
          item.object_ref.version_id,
          item.object_ref.sha256,
        ]),
      )
      .digest('hex') +
    '"'
  await page.route(`**/business/api/v1/assets/${assetId}`, (route) => route.fulfill({ json: item }))
  await connectBusiness(page, ['asset.read', 'asset.download'])
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await page.getByLabel('资产案件编号').fill(caseId)
  await page.getByLabel('资产详情编号').fill(assetId)
  await page.getByRole('button', { name: '读取资产详情' }).click()
  await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toBeEnabled()
  return { body, etag }
}

test('asset download transport fixture verifies fixed bytes before browser save', async ({
  page,
}) => {
  const { body, etag } = await openDownloadAsset(page)
  await page.route(`**/business/api/v1/assets/${assetId}/content`, (route) => {
    expect(route.request().method()).toBe('GET')
    expect(route.request().headers().authorization).toBe('Bearer self-owned-business-browser-token')
    expect(route.request().headers()['if-match']).toBeUndefined()
    return route.fulfill({ body, contentType: 'application/octet-stream', headers: { ETag: etag } })
  })
  const saved = page.waitForEvent('download')
  await page.getByRole('button', { name: '下载固定版本', exact: true }).click()
  expect((await saved).suggestedFilename()).toBe(`asset-${assetId}.bin`)
  await expect(
    page.getByRole('status').filter({ hasText: '已核验大小、SHA-256和固定对象版本' }),
  ).toBeVisible()
})

for (const mode of ['corrupt', '403', '503'])
  test(`asset download transport ${mode} never saves content`, async ({ page }) => {
    const { body, etag } = await openDownloadAsset(page)
    const saved: string[] = []
    page.on('download', (download) => saved.push(download.suggestedFilename()))
    await page.route(`**/business/api/v1/assets/${assetId}/content`, (route) =>
      mode === 'corrupt'
        ? route.fulfill({
            body: Buffer.alloc(body.length),
            contentType: 'application/octet-stream',
            headers: { ETag: etag },
          })
        : route.fulfill({ status: Number(mode), json: { code: 'SOURCE_AUTHORITY_UNAVAILABLE' } }),
    )
    await page.getByRole('button', { name: '下载固定版本', exact: true }).click()
    await expect(
      page
        .getByRole('status')
        .filter({ hasText: mode === 'corrupt' ? '核验未通过' : 'SOURCE_AUTHORITY_UNAVAILABLE' }),
    ).toBeVisible()
    expect(saved).toEqual([])
    await expect(page.getByText('已核验大小', { exact: false })).toHaveCount(0)
  })

test('asset download late transport response after selection clear cannot save', async ({
  page,
}) => {
  const { body, etag } = await openDownloadAsset(page)
  let release!: () => void
  const gate = new Promise<void>((resolve) => (release = resolve))
  let started!: () => void
  const observed = new Promise<void>((resolve) => (started = resolve))
  const saved: string[] = []
  page.on('download', (download) => saved.push(download.suggestedFilename()))
  await page.route(`**/business/api/v1/assets/${assetId}/content`, async (route) => {
    started()
    await gate
    await route.fulfill({ body, contentType: 'application/octet-stream', headers: { ETag: etag } })
  })
  await page.getByRole('button', { name: '下载固定版本', exact: true }).click()
  await observed
  await page.getByLabel('资产详情编号').fill(otherAssetId)
  const returned = page.waitForResponse((response) =>
    response.url().endsWith(`/assets/${assetId}/content`),
  )
  release()
  await returned
  await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toHaveCount(0)
  await expect(page.getByText('已核验大小', { exact: false })).toHaveCount(0)
  expect(saved).toEqual([])
})

test('catalog pages keep missing functional permission disabled without requesting lists', async ({
  page,
}) => {
  const requests: string[] = []
  await page.route('**/business/api/v1/assets?**', (route) => {
    requests.push(route.request().url())
    return route.abort()
  })
  await page.route('**/business/api/v1/analysis/tasks?**', (route) => {
    requests.push(route.request().url())
    return route.abort()
  })
  await connectBusiness(page, ['review.read'])
  await page.getByRole('link', { name: '资源库（媒体资产管理）', exact: true }).click()
  await expect(page.getByRole('button', { name: '查询资产／回到首页' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '读取资产详情' })).toBeDisabled()
  await page.getByRole('link', { name: '任务与结果', exact: true }).click()
  await expect(page.getByRole('button', { name: '查询任务／回到首页' })).toBeDisabled()
  expect(requests).toHaveLength(0)
})

// Self-owned upload routes test UI wiring; the local HTTP receiver below additionally
// records actual Chrome PUT bytes/Content-Length. Neither proves real business auth.
const browserUploadId = '81000000-0000-4000-8000-000000000001'
const browserAssetId = '82000000-0000-4000-8000-000000000001'
const uploadPermissions = ['source.read', 'asset.upload', 'asset.read']
const browserPng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j1ioAAAAASUVORK5CYII=',
  'base64',
)
const pngDigest = createHash('sha256').update(browserPng).digest('hex')
function uploadSource(): Schemas['Source'] {
  return { ...registeredSource(), authorization_status: 'verified', purpose: ['upload'] }
}
function browserUploadSession(
  state: Schemas['UploadSession']['state'] = 'UPLOADING',
): Schemas['UploadSession'] {
  return {
    upload_id: browserUploadId,
    part_size_bytes: 32,
    state,
    expires_at: '2099-01-01T00:00:00Z',
    version: 1,
  }
}
const pngParts = Array.from({ length: Math.ceil(browserPng.length / 32) }, (_, index) => {
  const bytes = browserPng.subarray(index * 32, (index + 1) * 32)
  return {
    part_no: index + 1,
    size_bytes: bytes.length,
    sha256: createHash('sha256').update(bytes).digest('hex'),
  }
})
async function prepareBusinessUpload(page: Page, sources = [uploadSource()]) {
  await page.route('**/business/api/v1/sources?**', (route) => {
    const url = new URL(route.request().url())
    expect(url.searchParams.get('case_id')).toBe(caseId)
    expect(url.searchParams.get('limit')).toBe('20')
    return route.fulfill({ json: { items: sources, next_cursor: null } })
  })
  await connectBusiness(page, uploadPermissions)
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await page.getByLabel('上传案件', { exact: true }).selectOption(caseId)
  await page.getByRole('button', { name: '查询上传来源', exact: true }).click()
  await page.getByLabel('上传来源', { exact: true }).selectOption(sourceId)
  await page
    .getByLabel('业务上传文件', { exact: true })
    .setInputFiles({ name: 'owned-one-pixel.png', mimeType: 'image/png', buffer: browserPng })
}

test('business upload requires identity and permission and only offers current case scope', async ({
  page,
}) => {
  let writes = 0
  await page.route('**/business/api/v1/uploads**', (route) => {
    writes++
    return route.abort()
  })
  await page.goto('/#/business/uploads')
  await expect(page.getByRole('button', { name: '初始化业务上传', exact: true })).toBeDisabled()
  await expect(page.getByLabel('上传案件', { exact: true })).toBeDisabled()
  await connectBusiness(page, ['source.read'])
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await expect(page.getByLabel('上传案件').locator('option')).toHaveCount(3)
  await expect(page.getByLabel('上传案件')).toHaveValue('')
  await expect(page.getByRole('button', { name: '初始化业务上传', exact: true })).toBeDisabled()
  await connectBusiness(page, uploadPermissions, [])
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await expect(page.getByLabel('上传案件')).toBeDisabled()
  await expect(page.getByLabel('上传案件').locator('option')).toHaveCount(1)
  await expect(page.getByText('当前无可用案件', { exact: false })).toBeVisible()
  expect(writes).toBe(0)
})

test('business upload filters sources by verified upload authorization', async ({ page }) => {
  const pending = {
    ...uploadSource(),
    source_id: '70000000-0000-4000-8000-000000000002',
    authorization_status: 'pending' as const,
  }
  const wrongPurpose = {
    ...uploadSource(),
    source_id: '70000000-0000-4000-8000-000000000003',
    purpose: ['analysis'],
  }
  await prepareBusinessUpload(page, [uploadSource(), pending, wrongPurpose])
  await expect(
    page.getByLabel('上传来源').locator(`option[value="${pending.source_id}"]:enabled`),
  ).toHaveCount(0)
  await expect(
    page.getByLabel('上传来源').locator(`option[value="${wrongPurpose.source_id}"]:enabled`),
  ).toHaveCount(0)
  await expect(page.getByLabel('浏览器摘要内存预算（MiB）')).toHaveValue('8')
})

test('business upload sends real Chrome binary PUT bytes and distinguishes accepted validation from valid asset', async ({
  page,
}) => {
  const received: {
    bytes: Buffer
    headers: Record<string, string | string[] | undefined>
    path: string
  }[] = []
  const receiver = createServer((req, res) => {
    const chunks: Buffer[] = []
    req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
    req.on('end', () => {
      const bytes = Buffer.concat(chunks)
      received.push({ bytes, headers: req.headers, path: req.url ?? '' })
      const partNo = Number(req.url?.split('/').at(-1))
      res.writeHead(200, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': 'http://127.0.0.1:14281',
      })
      res.end(JSON.stringify(pngParts[partNo - 1]))
    })
  })
  await new Promise<void>((resolve) => receiver.listen(0, '127.0.0.1', resolve))
  const address = receiver.address()
  if (!address || typeof address === 'string') throw new Error('receiver address unavailable')
  let complete = false
  let validated = false
  await page.route('**/business/api/v1/uploads**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    if (request.method() === 'PUT') {
      await route.continue({ url: `http://127.0.0.1:${address.port}${url.pathname}` })
    } else if (request.method() === 'POST' && url.pathname.endsWith('/uploads')) {
      expect(request.postDataJSON()).toEqual({
        case_id: caseId,
        source_id: sourceId,
        filename: 'owned-one-pixel.png',
        size_bytes: browserPng.length,
        mime: 'image/png',
        sha256: pngDigest,
      })
      expect(request.headers()['idempotency-key']).toBeTruthy()
      await route.fulfill({ status: 201, json: browserUploadSession() })
    } else if (url.pathname.endsWith('/complete')) {
      expect(request.postDataJSON()).toEqual({ parts: pngParts })
      complete = true
      await route.fulfill({
        status: 202,
        json: {
          upload_id: browserUploadId,
          asset_id: null,
          validation: 'VALIDATING',
          duplicate_of: null,
          request_id: taskId,
        },
      })
    } else if (url.pathname.endsWith('/parts')) {
      await route.fulfill({ json: { items: pngParts, next_cursor: null, session_version: 1 } })
    } else {
      await route.fulfill({
        json: {
          session: browserUploadSession(
            validated ? 'COMPLETED' : complete ? 'VALIDATING' : 'UPLOADING',
          ),
          result: complete
            ? {
                upload_id: browserUploadId,
                asset_id: validated ? browserAssetId : null,
                validation: validated ? 'VALID' : 'VALIDATING',
                duplicate_of: null,
                request_id: taskId,
              }
            : null,
          received_parts_count: received.length,
          received_bytes: received.reduce((sum, item) => sum + item.bytes.length, 0),
          total_size_bytes: browserPng.length,
        },
      })
    }
  })
  try {
    await prepareBusinessUpload(page)
    await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
    await page.getByRole('button', { name: '发送剩余分片', exact: true }).click()
    await expect.poll(() => received.length).toBe(pngParts.length)
    expect(Buffer.concat(received.map((item) => item.bytes))).toEqual(browserPng)
    for (const [index, item] of received.entries()) {
      expect(item.headers['content-length']).toBe(String(pngParts[index]!.size_bytes))
      expect(item.headers['content-type']).toBe('application/octet-stream')
      expect(item.headers['x-part-sha256']).toBe(pngParts[index]!.sha256)
      expect(item.headers['idempotency-key']).toBeTruthy()
      expect(item.headers.authorization).toBe('Bearer self-owned-business-browser-token')
    }
    await page.getByRole('button', { name: '核对服务端分片', exact: true }).click()
    await page.getByRole('button', { name: '完成上传并校验', exact: true }).click()
    await expect(page.getByRole('status')).toContainText('VALIDATING')
    await expect(page.getByText(browserAssetId, { exact: false })).toHaveCount(0)
    validated = true
    await page.getByRole('button', { name: '刷新校验进度', exact: true }).click()
    await expect(page.getByText(browserAssetId, { exact: false })).toBeVisible()
    const assetLink = page.getByRole('link', { name: '前往资产管理核对并读取', exact: true })
    const href = await assetLink.getAttribute('href')
    expect(href).toBeTruthy()
    const target = new URL(href!, page.url())
    const query = new URLSearchParams(target.hash.split('?')[1])
    expect(target.hash.split('?')[0]).toBe('#/assets')
    expect(query.get('case_id')).toBe(caseId)
    expect(query.get('asset_id')).toBe(browserAssetId)
  } finally {
    await new Promise<void>((resolve, reject) =>
      receiver.close((error) => (error ? reject(error) : resolve())),
    )
  }
})

test('business upload unknown create outcome retries original key and body', async ({ page }) => {
  const creates: { key: string | undefined; body: unknown }[] = []
  await page.route('**/business/api/v1/uploads', async (route) => {
    creates.push({
      key: route.request().headers()['idempotency-key'],
      body: route.request().postDataJSON(),
    })
    if (creates.length === 1) await route.abort('failed')
    else await route.fulfill({ status: 201, json: browserUploadSession() })
  })
  await prepareBusinessUpload(page)
  await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
  await expect(page.getByRole('button', { name: '重试原请求', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '重试原请求', exact: true }).click()
  await expect.poll(() => creates.length).toBe(2)
  expect(creates[1]).toEqual(creates[0])
  expect(creates[0]!.key).toBeTruthy()
})

test('business upload discards delayed initialization when identity is cleared after leaving', async ({
  page,
}) => {
  let release!: () => void
  let start!: () => void
  const waiting = new Promise<void>((resolve) => {
    release = resolve
  })
  const started = new Promise<void>((resolve) => {
    start = resolve
  })
  await page.route('**/business/api/v1/uploads', async (route) => {
    start()
    await waiting
    await route.fulfill({ status: 201, json: browserUploadSession() })
  })
  await prepareBusinessUpload(page)
  await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
  await started
  await expect(page.getByLabel('上传案件')).toBeDisabled()
  await expect(page.getByLabel('上传案件')).toHaveValue(caseId)
  await page.getByRole('link', { name: '业务身份', exact: true }).click()
  await page.getByRole('button', { name: '清除身份与结果', exact: true }).click()
  release()
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await expect(page.getByLabel('上传案件')).toHaveValue('')
  await expect(page.getByLabel('上传案件').locator('option')).toHaveCount(1)
  await expect(page.getByText(browserUploadId, { exact: false })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '发送剩余分片', exact: true })).toBeDisabled()
})

test('business upload unknown part outcome retries original bytes digest and key', async ({
  page,
}) => {
  const attempts: { key: string | undefined; digest: string | undefined; bytes: string }[] = []
  await page.route('**/business/api/v1/uploads**', async (route) => {
    const request = route.request()
    if (request.method() === 'POST')
      return route.fulfill({ status: 201, json: browserUploadSession() })
    if (request.method() === 'PUT') {
      const partNo = Number(new URL(request.url()).pathname.split('/').at(-1))
      attempts.push({
        key: request.headers()['idempotency-key'],
        digest: request.headers()['x-part-sha256'],
        bytes: request.postDataBuffer()!.toString('hex'),
      })
      if (attempts.length === 1) return route.abort('failed')
      return route.fulfill({ json: pngParts[partNo - 1] })
    }
    return route.fulfill({ json: { items: [], next_cursor: null, session_version: 1 } })
  })
  await prepareBusinessUpload(page)
  await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
  await page.getByRole('button', { name: '发送剩余分片', exact: true }).click()
  await expect(page.getByRole('button', { name: '重试原请求', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '重试原请求', exact: true }).click()
  await expect.poll(() => attempts.length).toBeGreaterThanOrEqual(2)
  expect(attempts[1]).toEqual(attempts[0])
  expect(attempts[0]!.key).toBeTruthy()
  expect(attempts[0]!.digest).toBe(pngParts[0]!.sha256)
  expect(attempts[0]!.bytes).toBe(browserPng.subarray(0, 32).toString('hex'))
})

test('business upload case changes immediately clear selected source and local file', async ({
  page,
}) => {
  let writes = 0
  await page.route('**/business/api/v1/uploads**', (route) => {
    writes++
    return route.abort()
  })
  await prepareBusinessUpload(page)
  await expect(page.getByLabel('上传来源')).toHaveValue(sourceId)
  await page.getByLabel('上传案件').selectOption(otherCaseId)
  await expect(page.getByLabel('上传来源')).toHaveValue('')
  await expect(page.getByLabel('业务上传文件')).toHaveValue('')
  await expect(page.getByRole('button', { name: '初始化业务上传', exact: true })).toBeDisabled()
  expect(writes).toBe(0)
})

test('business upload leaving alone discards late response while keeping connected identity', async ({
  page,
}) => {
  let release!: () => void
  let start!: () => void
  let finish!: () => void
  const waiting = new Promise<void>((resolve) => {
    release = resolve
  })
  const started = new Promise<void>((resolve) => {
    start = resolve
  })
  const finished = new Promise<void>((resolve) => {
    finish = resolve
  })
  await page.route('**/business/api/v1/uploads', async (route) => {
    start()
    await waiting
    await route.fulfill({ status: 201, json: browserUploadSession() })
    finish()
  })
  await prepareBusinessUpload(page)
  await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
  await started
  await page.getByRole('link', { name: '业务身份', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('业务身份已连接')
  release()
  await finished
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await expect(page.getByLabel('上传案件')).toHaveValue('')
  await expect(page.getByLabel('上传案件').locator('option')).toHaveCount(3)
  await expect(page.getByLabel('业务上传文件')).toHaveValue('')
  await expect(page.getByText(browserUploadId, { exact: false })).toHaveCount(0)
  await expect(page.getByRole('button', { name: '发送剩余分片', exact: true })).toBeDisabled()
})
