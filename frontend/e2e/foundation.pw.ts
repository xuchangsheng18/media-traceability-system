import { expect, test, type Page } from '@playwright/test'

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
async function connectBusiness(page: Page) {
  await page.route('**/business/api/v1/auth/me', (route) =>
    route.fulfill({
      json: {
        user_id: '44444444-4444-4444-8444-444444444444',
        org_id: '55555555-5555-4555-8555-555555555555',
        roles: ['self-owned-browser-fixture'],
        permissions: ['task.read', 'review.read'],
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
  await page.getByRole('link', { name: '待复核队列', exact: true }).click()
  await expect(page.getByRole('heading', { name: '待复核队列', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '查询待复核' })).toBeDisabled()
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
  await page.getByRole('link', { name: '待复核队列', exact: true }).click()
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
