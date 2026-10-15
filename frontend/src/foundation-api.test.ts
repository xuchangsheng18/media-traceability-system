import { afterEach, expect, test, vi } from 'vitest'
import { request } from './api'
import viteConfig from '../vite.config'
import { createServer as createHttpServer } from 'node:http'
import { createServer as createViteServer } from 'vite'

test('development proxy forwards both health and existing upload paths', async () => {
  expect(viteConfig.server?.proxy?.['/api']).toBe('http://127.0.0.1:14200')
  expect(viteConfig.server?.proxy?.['/poc']).toBe('http://127.0.0.1:14200')
  const backend = createHttpServer((incoming, response) => {
    response.setHeader('Content-Type', 'application/json')
    response.end(
      JSON.stringify({ path: incoming.url, authorization: incoming.headers.authorization }),
    )
  })
  await new Promise<void>((resolve) => backend.listen(0, '127.0.0.1', resolve))
  const address = backend.address()
  if (!address || typeof address === 'string') throw new Error('SELF_OWNED_TEST_SERVER_MISSING')
  const target = `http://127.0.0.1:${address.port}`
  const server = await createViteServer({
    configFile: false,
    server: {
      host: '127.0.0.1',
      port: 0,
      proxy: Object.fromEntries(
        Object.keys(viteConfig.server?.proxy ?? {}).map((key) => [key, target]),
      ),
    },
  })
  try {
    await server.listen()
    const viteAddress = server.httpServer?.address()
    if (!viteAddress || typeof viteAddress === 'string') throw new Error('SELF_OWNED_VITE_MISSING')
    for (const path of ['/api/v1/health', '/poc/assets']) {
      const response = await fetch(`http://127.0.0.1:${viteAddress.port}${path}`, {
        headers: { Authorization: 'Bearer self-owned-proxy-test' },
      })
      expect(await response.json()).toEqual({ path, authorization: 'Bearer self-owned-proxy-test' })
    }
  } finally {
    await server.close()
    await new Promise<void>((resolve) => backend.close(() => resolve()))
  }
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

test('configured API base preserves prefix and submitted authentication', async () => {
  vi.stubEnv('VITE_API_BASE_URL', 'https://example.invalid/root')
  const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
    ok: true,
    json: async () => ({ status: 'ok' }),
  }))
  vi.stubGlobal('fetch', fetch)
  await request('/poc/jobs', 'self-owned-token')
  expect(fetch.mock.calls[0]?.[0]).toBe('https://example.invalid/root/poc/jobs')
})

test.each(['//other.invalid/poc', 'https://other.invalid/poc', '/poc/../admin'])(
  'unsafe request path %s is rejected before sending a token',
  async (path) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    await expect(request(path, 'self-owned-token')).rejects.toThrow('API_PATH_INVALID')
    expect(fetch).not.toHaveBeenCalled()
  },
)

test.each([
  'javascript:alert(1)',
  'https://user:password@example.invalid',
  '/prefix?token=private',
  'https://example.invalid/root/../admin',
  'https://example.invalid/root/%2e%2e/admin',
  'https://example.invalid/root/\nadmin',
  '/prefix/\nadmin',
])('invalid API base %s is rejected', async (base) => {
  vi.stubEnv('VITE_API_BASE_URL', base)
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  await expect(request('/poc/jobs', 'self-owned-token')).rejects.toThrow('API_BASE_INVALID')
  expect(fetch).not.toHaveBeenCalled()
})

test('safe error code and request id are available without echoing a private server message', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: false,
      status: 503,
      json: async () => ({
        code: 'DATABASE_UNAVAILABLE',
        message: 'private-server-message',
        request_id: '10000000-0000-4000-8000-000000000001',
      }),
    })),
  )
  await expect(request('/poc/jobs', 'self-owned-token')).rejects.toMatchObject({
    status: 503,
    code: 'DATABASE_UNAVAILABLE',
    requestId: '10000000-0000-4000-8000-000000000001',
  })
})
