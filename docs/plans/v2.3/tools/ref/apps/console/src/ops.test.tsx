import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { assertNoSecretsInBundle } from './api/client'
import { OpsPanel } from './components/OpsPanel'
import { MOCK_OPS } from './data/fixtures'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const WORKERS = [
  {
    workerId: 'wk_1',
    status: 'idle',
    generation: 1,
    capacity: 1,
    privacy: [],
    claimed: null,
    activeLeases: [],
    revoked: false,
  },
]

function stubFetch(routes: Record<string, { status: number; body?: unknown }>) {
  const calls: Array<{ url: string; method: string }> = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input)
      calls.push({ url, method: init?.method ?? 'GET' })
      const key = Object.keys(routes).find((k) => url.endsWith(k))
      if (!key) return new Response('{}', { status: 404 })
      const r = routes[key]
      return new Response(JSON.stringify(r.body ?? {}), { status: r.status })
    }),
  )
  return calls
}

describe('ops tab', () => {
  it('mock fixture is secret-free', () => {
    assertNoSecretsInBundle(MOCK_OPS)
    expect(MOCK_OPS.mode).toBe('mock')
  })

  it('mock mode shows fixture ops and disables controls', async () => {
    vi.stubGlobal('location', { ...window.location, search: '?mode=mock' })
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Ops' }))
    expect(await screen.findByTestId('ops-event-oev_mock_1')).toBeInTheDocument()
    expect(screen.getByTestId('ops-queue-proj_demo')).toBeInTheDocument()
    expect(screen.getByTestId('worker-controls-mock')).toBeInTheDocument()
  })

  it('live mode never shows fixtures and reports missing queues honestly', async () => {
    stubFetch({
      '/v1/ops/events': {
        status: 200,
        body: {
          events: [
            { event_id: 'oev_live', kind: 'mission.created', component: 'api', project_id: 'p', at: 'x' },
          ],
        },
      },
    })
    render(<OpsPanel mode="live" baseUrl="http://api.test" workers={WORKERS} />)
    expect(await screen.findByTestId('ops-event-oev_live')).toBeInTheDocument()
    expect(screen.queryByTestId('ops-event-oev_mock_1')).toBeNull()
    expect(screen.getByTestId('ops-queues-unavailable')).toBeInTheDocument()
  })

  it('drain posts to the API and shows the new state', async () => {
    const calls = stubFetch({
      '/v1/ops/events': { status: 200, body: { events: [] } },
      '/v1/scheduler/queues': { status: 200, body: { projects: [] } },
      '/v1/workers/wk_1/drain': { status: 200, body: { worker_id: 'wk_1', drain_state: 'draining' } },
    })
    render(<OpsPanel mode="live" baseUrl="http://api.test" token="atk_policy_demo" workers={WORKERS} />)
    await screen.findByTestId('ops-no-events')
    await userEvent.click(screen.getByTestId('drain-wk_1'))
    expect(await screen.findByTestId('worker-controls-note')).toHaveTextContent('wk_1 → draining')
    expect(calls.some((c) => c.url.endsWith('/v1/workers/wk_1/drain') && c.method === 'POST')).toBe(
      true,
    )
  })

  it('revoke on a server without the route says not available', async () => {
    stubFetch({ '/v1/ops/events': { status: 200, body: { events: [] } } })
    render(<OpsPanel mode="live" baseUrl="http://api.test" workers={WORKERS} />)
    await screen.findByTestId('ops-no-events')
    await userEvent.click(screen.getByTestId('revoke-wk_1'))
    expect(await screen.findByTestId('worker-controls-note')).toHaveTextContent(
      'Revoke not available on this server',
    )
  })
})
