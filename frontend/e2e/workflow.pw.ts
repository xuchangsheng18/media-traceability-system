import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
test('browser submits image and displays a real CPU result', async ({ page }) => {
  const credentials = JSON.parse(readFileSync('/workspace/glwy/runtime/media-traceability-system/credentials.json', 'utf8'))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '媒体溯源研发验证台' })).toBeVisible()
  await page.getByLabel('研发访问令牌').fill(credentials.api_token)
  await page.getByLabel('测试图片').setInputFiles(fileURLToPath(new URL('./fixture.png', import.meta.url)))
  await page.getByRole('button', { name: '开始验证' }).click()
  await expect(page.getByRole('status')).toHaveText('SUCCEEDED', { timeout: 60000 })
  await expect(page.getByTestId('result')).toContainText('synthetic-cpu-encoder')
  await expect(page.getByTestId('result')).toContainText('"mock": false')
  await page.getByLabel('研发访问令牌').fill('')
  await page.screenshot({ path: fileURLToPath(new URL('../../docs/00-project/validation/poc-ui.png', import.meta.url)), fullPage: true })
})
