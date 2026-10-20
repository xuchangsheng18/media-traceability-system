import { afterEach, expect, test, vi } from 'vitest'
import { BusinessClient, pageQuery } from './api'
import { createBusinessSession } from './session'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

test('business identity is required before any network request', async () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  await expect(new BusinessClient().call('/auth/me')).rejects.toThrow('401')
  expect(fetch).not.toHaveBeenCalled()
})

test('business calls have a separate proxy, no cookies or redirect, and exact mutation headers', async () => {
  const fetch = vi.fn(
    async (_url: string, _options: RequestInit) =>
      new Response('{"version":2}', { headers: { ETag: '"v2"' } }),
  )
  vi.stubGlobal('fetch', fetch)
  const client = new BusinessClient()
  client.replaceToken('self-owned-business-token')
  const response = await client.call(
    '/approvals/id/decisions',
    { expected_version: 1 },
    'fixed-key',
    '"v1"',
  )
  expect(fetch.mock.calls[0]?.[0]).toBe('/business/api/v1/approvals/id/decisions')
  expect(fetch.mock.calls[0]?.[1]).toMatchObject({
    credentials: 'omit',
    redirect: 'error',
    cache: 'no-store',
    method: 'POST',
    headers: {
      Authorization: 'Bearer self-owned-business-token',
      'Idempotency-Key': 'fixed-key',
      'If-Match': '"v1"',
    },
  })
  expect(response.etag).toBe('"v2"')
})

test.each(['//outside.invalid', '/x/../admin', 'https://outside.invalid', '/x#fragment'])(
  'unsafe business path %s never receives a bearer',
  async (path) => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const client = new BusinessClient()
    client.replaceToken('self-owned-token')
    await expect(client.call(path)).rejects.toThrow()
    expect(fetch).not.toHaveBeenCalled()
  },
)

test('identity switch rejects a late response even if transport ignores cancellation', async () => {
  let finish!: (response: Response) => void
  vi.stubGlobal(
    'fetch',
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve
        }),
    ),
  )
  const client = new BusinessClient()
  client.replaceToken('self-owned-old-token')
  const promise = client.call('/audit/events')
  const result = expect(promise).rejects.toThrow('身份已切换')
  client.replaceToken('self-owned-new-token')
  finish(new Response('{"items":["old-private-result"]}'))
  await result
})

test('missing business policies remain a failed request', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('{"code":"FORMAL_POLICY_UNCONFIGURED"}', { status: 503 })),
  )
  const client = new BusinessClient()
  client.replaceToken('self-owned-token')
  await expect(client.call('/approvals')).rejects.toThrow('503')
})

test('a changed identity cannot retain the previous user or privileges on connection failure', async () => {
  const session = createBusinessSession()
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            user_id: 'first',
            org_id: 'unit',
            permissions: ['audit.read'],
            roles: ['auditor'],
            case_ids: [],
          }),
        ),
    ),
  )
  await session.connect('self-owned-first')
  expect(session.has('audit.read')).toBe(true)
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('{}', { status: 401 })),
  )
  await session.connect('self-owned-second')
  expect(session.state.user).toBeNull()
  expect(session.has('audit.read')).toBe(false)
  expect(session.state.busy).toBe(false)
})

test('case and cursor are encoded as query fields rather than path fragments', () => {
  const id = '10000000-0000-4000-8000-000000000001'
  expect(pageQuery(id, 20, 'a+b/c=')).toBe(`case_id=${id}&limit=20&cursor=a%2Bb%2Fc%3D`)
  expect(() => pageQuery('../other', 20)).toThrow()
})
