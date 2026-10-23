// No intercepted API responses: the Python harness owns isolated synthetic trust.
import { chromium, expect } from '@playwright/test'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { URL, URLSearchParams } from 'node:url'
import console from 'node:console'

let input = ''
for await (const chunk of process.stdin) input += chunk
const config = JSON.parse(input)
const browser = await chromium.launch({
  headless: true,
  ...(process.env.MT_TEST_BROWSER_EXECUTABLE
    ? { executablePath: process.env.MT_TEST_BROWSER_EXECUTABLE }
    : {}),
})
try {
  const page = await browser.newPage({ acceptDownloads: true })
  page.setDefaultTimeout(20000)
  const parts = []
  page.on('response', (response) => {
    if (
      /\/uploads\/[^/]+\/parts\/\d+$/.test(response.url()) &&
      response.request().method() === 'PUT'
    )
      parts.push(response.status())
  })
  const denied = await page.request.get(config.origin + '/business/api/v1/auth/me')
  expect(denied.status()).toBe(401)
  await page.goto(config.origin + '/#/business')
  await page.getByLabel('业务访问令牌', { exact: true }).fill('test-only-valid-token')
  await page.getByRole('button', { name: '连接身份', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('业务身份已连接')
  await page.getByRole('link', { name: '业务上传', exact: true }).click()
  await page.getByLabel('上传案件', { exact: true }).selectOption(config.case_id)
  await page.getByRole('button', { name: '查询上传来源', exact: true }).click()
  await page.getByLabel('上传来源', { exact: true }).selectOption(config.source_id)
  await page.getByLabel('业务上传文件', { exact: true }).setInputFiles(config.image)
  await expect(page.getByRole('button', { name: '初始化业务上传', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '初始化业务上传', exact: true }).click()
  await page.getByRole('button', { name: '发送剩余分片', exact: true }).click()
  await expect(page.getByRole('button', { name: '完成上传并校验', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '核对服务端分片', exact: true }).click()
  await expect(page.getByRole('button', { name: '完成上传并校验', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: '完成上传并校验', exact: true }).click()
  const asset = page.getByRole('link', { name: '前往资产管理核对并读取', exact: true })
  await expect(asset).toBeVisible()
  const target = new URL(await asset.getAttribute('href'), config.origin)
  const assetId = new URLSearchParams(target.hash.split('?')[1]).get('asset_id')
  expect(assetId).toBeTruthy()
  await asset.click()
  await page.getByRole('button', { name: '读取资产详情', exact: true }).click()
  await expect(page.getByRole('button', { name: '下载固定版本', exact: true })).toBeEnabled()
  const waiting = page.waitForEvent('download')
  void waiting.catch(() => {})
  const content = page.waitForResponse((response) =>
    response.url().endsWith(`/assets/${assetId}/content`),
  )
  await page.getByRole('button', { name: '下载固定版本', exact: true }).click()
  const reply = await content
  expect(reply.status(), await reply.text()).toBe(200)
  await expect(
    page.getByRole('status').filter({ hasText: '已核验大小、SHA-256和固定对象版本' }),
  ).toBeVisible()
  const download = await waiting
  const downloaded = await readFile(await download.path())
  const digest = createHash('sha256').update(downloaded).digest('hex')
  expect(digest).toBe(config.sha256)
  await page.getByRole('button', { name: '查询资产／回到首页', exact: true }).click()
  await expect(page.getByRole('cell', { name: assetId, exact: true })).toBeVisible()
  expect(parts).toEqual([200, 200, 200])
  console.log(
    JSON.stringify({
      status: 'PASS_REAL_TRANSPORT_SYNTHETIC_TRUST',
      asset_id: assetId,
      download_sha256: digest,
      part_count: parts.length,
    }),
  )
} finally {
  await browser.close()
}
