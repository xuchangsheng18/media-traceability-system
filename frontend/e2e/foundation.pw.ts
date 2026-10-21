import { expect, test, type Page } from '@playwright/test'
import type { Schemas } from '../src/business/api'

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
) {
  await page.route('**/business/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        user_id: '44444444-4444-4444-8444-444444444444',
        org_id: '55555555-5555-4555-8555-555555555555',
        roles: ['self-owned-browser-fixture'],
        permissions,
        case_ids: [caseId, otherCaseId],
      },
    }),
  )
  await page.goto('/#/business')
  await page.getByLabel('业务访问令牌').fill('self-owned-business-browser-token')
  await page.getByRole('button', { name: '连接身份', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('业务身份已连接')
  await expect(page.getByLabel('业务访问令牌')).toHaveValue('')
}

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
  await expect(
    page.getByText('完整血缘、来源授权明细及受控下载尚未接入本页', { exact: false }),
  ).toBeVisible()
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
