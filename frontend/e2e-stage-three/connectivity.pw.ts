import { expect, test } from '@playwright/test'
test('Vue page reaches backend and marked mock inference', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '检查服务' }).click()
  await expect(page.getByRole('status')).toHaveText('页面、接口和模拟推理服务均已连通')
  await expect(page.getByTestId('mock-label')).toHaveText('模拟结果，仅用于连接验证')
})
