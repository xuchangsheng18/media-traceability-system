import { expect, test } from '@playwright/test'

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
