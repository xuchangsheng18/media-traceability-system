import { expect, test, vi } from 'vitest'
import { request } from './api'
test('HTTP rejection is not returned as a successful job', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 401 })),
  )
  await expect(request('/poc/jobs/x', 'invalid')).rejects.toThrow('401')
  vi.unstubAllGlobals()
})
test('idempotency and auth headers are sent with the submitted asset', async () => {
  const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
    ok: true,
    json: async () => ({ job_id: 'x' }),
  }))
  vi.stubGlobal('fetch', fetch)
  await request('/poc/jobs', 'test-token', { asset_id: 'asset' }, 'key')
  expect(fetch.mock.calls[0]?.[1]).toMatchObject({
    headers: { 'Idempotency-Key': 'key', Authorization: 'Bearer test-token' },
  })
  vi.unstubAllGlobals()
})
