import { afterEach, expect, test, vi } from 'vitest'
import { createBusinessSession } from './session'

afterEach(() => vi.unstubAllGlobals())

const cases = (['GET', 'POST', 'binary'] as const).flatMap((kind) =>
  ([true, false] as const).map((authenticated) => ({ kind, authenticated })),
)
test.each(cases)(
  'a settled old 401 preserves a new connection attempt ($kind, authenticated=$authenticated)',
  async ({ kind, authenticated }) => {
    const session = createBusinessSession()
    let connecting: Promise<void> | undefined
    let finishIdentity!: (response: Response) => void
    let began!: () => void
    const started = new Promise<void>((resolve) => (began = resolve))
    const fetch = vi.fn(async (url: string, options: RequestInit) => {
      if (url.endsWith('/auth/me')) {
        const token = new Headers(options.headers).get('Authorization')
        if (token === 'Bearer self-owned-new-token') {
          began()
          return new Promise<Response>((resolve) => (finishIdentity = resolve))
        }
        return Response.json({
          user_id: 'old',
          org_id: 'unit',
          permissions: ['asset.read'],
          roles: ['analyst'],
          case_ids: [],
        })
      }
      if (url.endsWith('/current-probe')) return Response.json({ current: true })
      const response = Response.json({ code: 'AUTHENTICATION_REQUIRED' }, { status: 401 })
      const json = response.json.bind(response)
      response.json = async () => {
        const problem: unknown = await json()
        // Controlled shared-API scheduling: after the real client's final version check,
        // before its rejected Promise reaches session.call. Not a normal UI-click race.
        queueMicrotask(() =>
          queueMicrotask(() =>
            queueMicrotask(() => {
              connecting = session.connect('self-owned-new-token')
            }),
          ),
        )
        return problem
      }
      return response
    })
    vi.stubGlobal('fetch', fetch)
    await session.connect('self-owned-old-token')
    const previous = session
      .call(
        '/self-owned-old-request',
        kind === 'POST' ? { expected_version: 1 } : undefined,
        kind === 'POST' ? 'self-owned-fixed-key' : undefined,
        undefined,
        kind === 'binary',
      )
      .catch((error: unknown) => error)
    await started
    const generation = session.state.generation
    const oldError = await previous
    const afterOld = {
      generation: session.state.generation,
      busy: session.state.busy,
      user: session.state.user,
      message: session.state.message,
    }
    finishIdentity(
      authenticated
        ? Response.json({
            user_id: 'new',
            org_id: 'unit',
            permissions: ['asset.read'],
            roles: ['analyst'],
            case_ids: [],
          })
        : Response.json({ code: 'AUTHENTICATION_REQUIRED' }, { status: 401 }),
    )
    await connecting
    expect(oldError).toMatchObject({ status: 401, code: 'AUTHENTICATION_REQUIRED' })
    expect(afterOld.generation).toBe(generation)
    expect(afterOld.busy).toBe(true)
    expect(afterOld.user).toBeNull()
    expect(session.state.busy).toBe(false)
    if (authenticated) {
      expect(session.state.generation).toBe(generation)
      expect(session.state.user?.user_id).toBe('new')
      expect(session.has('asset.read')).toBe(true)
      await expect(session.call('/current-probe')).resolves.toMatchObject({
        data: { current: true },
      })
      expect(new Headers(fetch.mock.lastCall?.[1].headers).get('Authorization')).toBe(
        'Bearer self-owned-new-token',
      )
    } else {
      expect(session.state.generation).toBe(generation + 1)
      expect(session.state.user).toBeNull()
      expect(session.has('asset.read')).toBe(false)
      expect(session.state.message).toContain('AUTHENTICATION_REQUIRED')
    }
  },
)
