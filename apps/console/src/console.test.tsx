import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import {
  scrubSecrets,
  assertNoSecretsInBundle,
  loadSnapshot,
  emptyLiveSnapshot,
  resolveConsoleLoadOpts,
} from './api/client'
import { MOCK_SNAPSHOT, expandMission, contractMission, interruptStream } from './data/fixtures'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function stubMockMode() {
  vi.stubGlobal('location', {
    ...window.location,
    search: '?mode=mock',
  })
}

describe('console fixtures', () => {
  it('labels mock mode and never carries secret-shaped strings', () => {
    assertNoSecretsInBundle(MOCK_SNAPSHOT)
    expect(MOCK_SNAPSHOT.mode).toBe('mock')
    expect(scrubSecrets('Bearer sk-abc123xyz')).toContain('[redacted]')
  })

  it('expands and contracts mission graph', () => {
    const expanded = expandMission(MOCK_SNAPSHOT)
    expect(expanded.mission.tasks.length).toBeGreaterThan(MOCK_SNAPSHOT.mission.tasks.length)
    const contracted = contractMission(expanded)
    expect(contracted.mission.tasks.length).toBeLessThanOrEqual(expanded.mission.tasks.length)
  })

  it('marks stream interrupts for reconnect', () => {
    const interrupted = interruptStream(MOCK_SNAPSHOT)
    expect(interrupted.streamInterrupted).toBe(true)
    expect(interrupted.errors[0]).toMatch(/cursor/)
  })

  it('live mode uses durable API missions without fixture mission id', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input)
        if (url.endsWith('/health/ready')) {
          return new Response(JSON.stringify({ status: 'ready', database: 'up' }), { status: 200 })
        }
        if (url.endsWith('/v1/capacity')) {
          return new Response(
            JSON.stringify({
              buckets: [],
              mock_vs_live: 'observed_or_empty_not_mock_broker',
            }),
            { status: 200 },
          )
        }
        if (url.endsWith('/v1/missions')) {
          return new Response(
            JSON.stringify({
              missions: [
                {
                  mission_id: 'msn_live_shared',
                  project_id: 'proj_a',
                  objective: 'unfamiliar live goal',
                  status: 'planning',
                  source: 'mission_store',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/missions/msn_live_shared/artifacts')) {
          return new Response(
            JSON.stringify({
              artifacts: [
                {
                  artifact_id: 'art_live_1',
                  kind: 'result',
                  content_hash: 'abc123deadbeef',
                  byte_length: 12,
                  summary: 'live artifact',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/missions/msn_live_shared/graph')) {
          return new Response(
            JSON.stringify({
              mission_id: 'msn_live_shared',
              tasks: [{ id: 'tsk_1', objective: 'extract', status: 'ready' }],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/events')) {
          return new Response(JSON.stringify({ items: [] }), { status: 200 })
        }
        if (url.includes('/v1/missions/msn_live_shared')) {
          return new Response(
            JSON.stringify({
              mission: {
                id: 'msn_live_shared',
                project_id: 'proj_a',
                objective: 'unfamiliar live goal',
                status: 'planning',
                revision: 2,
              },
            }),
            { status: 200 },
          )
        }
        if (url.endsWith('/v1/projects')) {
          return new Response(
            JSON.stringify({
              projects: [
                {
                  project_id: 'proj_a',
                  name: 'Live proj',
                  repo_path: '/app',
                  allow_paid: false,
                  allowed_tools: [],
                  updated_at: '2026-09-25T00:00:00Z',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.endsWith('/v1/routes') || url.endsWith('/v1/workers')) {
          return new Response(
            JSON.stringify({
              routes: [],
              workers: [
                {
                  worker_id: 'wk_live_1',
                  status: 'online',
                  generation: 1,
                  capacity: 1,
                  privacy: ['local'],
                  claimed: null,
                  revoked: false,
                },
              ],
            }),
            { status: 200 },
          )
        }
        return new Response('missing', { status: 404 })
      }),
    )
    const snap = await loadSnapshot({ mode: 'live', baseUrl: 'http://127.0.0.1:9' })
    expect(snap.mode).toBe('live')
    expect(snap.hostnamePublic).toBe('swarm.splitsignal.ai')
    expect(snap.serverReady).toBe(true)
    expect(snap.mission.missionId).toBe('msn_live_shared')
    expect(snap.mission.objective).toBe('unfamiliar live goal')
    expect(snap.mission.tasks).toHaveLength(1)
    expect(snap.history[0]?.missionId).toBe('msn_live_shared')
    expect(snap.artifacts[0]?.contentHash).toBe('abc123deadbeef')
    expect(snap.projects[0]?.projectId).toBe('proj_a')
    expect(snap.workers[0]?.workerId).toBe('wk_live_1')
    expect(snap.routes).toEqual([])
    expect(snap.profiles).toEqual([])
    expect(snap.mockVsLive).not.toContain('fixtures_only')
    expect(snap.mockVsLive).not.toContain('fixture-labeled')
  })

  it('live mode respects missionId selection for artifacts', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input)
        if (url.endsWith('/health/ready')) {
          return new Response(JSON.stringify({ status: 'ready' }), { status: 200 })
        }
        if (url.endsWith('/v1/capacity')) {
          return new Response(JSON.stringify({ buckets: [] }), { status: 200 })
        }
        if (url.endsWith('/v1/missions')) {
          return new Response(
            JSON.stringify({
              missions: [
                { mission_id: 'msn_a', objective: 'A', status: 'planning' },
                { mission_id: 'msn_b', objective: 'B', status: 'completed' },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/missions/msn_b/artifacts')) {
          return new Response(
            JSON.stringify({
              artifacts: [{ artifact_id: 'art_b', kind: 'result', content_hash: 'hash_b' }],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/missions/msn_b/graph')) {
          return new Response(JSON.stringify({ tasks: [] }), { status: 200 })
        }
        if (url.includes('/v1/missions/msn_b')) {
          return new Response(
            JSON.stringify({
              mission: { id: 'msn_b', objective: 'B', status: 'completed', revision: 3 },
            }),
            { status: 200 },
          )
        }
        if (url.includes('/v1/events') || url.endsWith('/v1/routes') || url.endsWith('/v1/workers') || url.endsWith('/v1/projects')) {
          return new Response(JSON.stringify({ items: [], routes: [], workers: [], projects: [] }), {
            status: 200,
          })
        }
        return new Response('missing', { status: 404 })
      }),
    )
    const snap = await loadSnapshot({
      mode: 'live',
      baseUrl: 'http://127.0.0.1:9',
      missionId: 'msn_b',
    })
    expect(snap.mission.missionId).toBe('msn_b')
    expect(snap.artifacts[0]?.contentHash).toBe('hash_b')
  })

  it('live mode without baseUrl is honest empty not mock fixtures', async () => {
    const snap = await loadSnapshot({ mode: 'live' })
    expect(snap.mode).toBe('live')
    expect(snap.mission.missionId).toBe('(none)')
    expect(snap.routes).toEqual([])
    expect(snap.workers).toEqual([])
    expect(snap.mockVsLive).not.toContain('fixtures_only')
  })

  it('default resolveConsoleLoadOpts is live not mock', () => {
    vi.stubGlobal('location', { ...window.location, search: '' })
    expect(resolveConsoleLoadOpts().mode).toBe('live')
    vi.stubGlobal('location', { ...window.location, search: '?mode=mock' })
    expect(resolveConsoleLoadOpts().mode).toBe('mock')
  })

  it('emptyLiveSnapshot never embeds MOCK_SNAPSHOT routes', () => {
    const snap = emptyLiveSnapshot()
    expect(snap.routes).toEqual([])
    expect(snap.mode).toBe('live')
    assertNoSecretsInBundle(snap)
  })
})

describe('operator console UI (fixture mode)', () => {
  beforeEach(() => {
    stubMockMode()
  })

  it('shows mission waiting reasons and expand/contract', async () => {
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByTestId('mode-banner')).toHaveTextContent('MOCK')
    expect(screen.getByTestId('mission-panel')).toBeInTheDocument()
    expect(screen.getByText(/inference quota exhausted/i)).toBeInTheDocument()
    const before = screen.getAllByTestId(/task-row-/).length
    await user.click(screen.getByTestId('expand-mission'))
    expect(screen.getAllByTestId(/task-row-/).length).toBeGreaterThan(before)
    await user.click(screen.getByTestId('contract-mission'))
  })

  it('shows exhausted, unknown, retired, gated routes without inventing available', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Routes' }))
    const panel = await screen.findByTestId('routes-panel')
    expect(within(panel).getByTestId('badge-exhausted')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-unknown')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-retired')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-gated')).toBeInTheDocument()
  })

  it('shows unknown capacity remaining honestly', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Capacity' }))
    expect(await screen.findByTestId('remaining-qb_tokens')).toHaveTextContent('unknown')
    expect(screen.getByTestId('remaining-qb_demo_requests')).toHaveTextContent('0')
  })

  it('distinguishes qualified vs provisional profiles', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Profiles' }))
    const panel = await screen.findByTestId('profiles-panel')
    expect(within(panel).getByTestId('badge-qualified')).toBeInTheDocument()
    expect(within(panel).getByTestId('badge-provisional')).toBeInTheDocument()
  })

  it('shows approval payload details', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Approvals' }))
    expect(await screen.findByTestId('approval-payload')).toHaveTextContent('tool.network')
  })

  it('handles interrupted event stream and stale workers', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Workers' }))
    expect(await screen.findByTestId('badge-stale')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Events' }))
    await user.click(screen.getByTestId('interrupt-stream'))
    expect(screen.getByTestId('stream-interrupted')).toBeInTheDocument()
    expect(screen.getByTestId('error-banner')).toBeInTheDocument()
  })

  it('shows projects, history, and artifacts panels', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.click(screen.getByRole('button', { name: 'Projects' }))
    expect(await screen.findByTestId('projects-panel')).toBeInTheDocument()
    expect(screen.getByTestId('project-proj_demo')).toHaveTextContent('Demo workspace')
    await user.click(screen.getByRole('button', { name: 'History' }))
    expect(await screen.findByTestId('history-panel')).toBeInTheDocument()
    expect(screen.getByTestId('history-mission_demo_001')).toHaveTextContent('zero_spend')
    await user.click(screen.getByRole('button', { name: 'Artifacts' }))
    expect(await screen.findByTestId('artifacts-panel')).toBeInTheDocument()
    expect(screen.getByTestId('artifact-art_journey_note')).toHaveTextContent('markdown')
  })

  it('supports keyboard tab navigation to sections', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByTestId('mission-panel')
    await user.tab()
    const routes = screen.getByRole('button', { name: 'Routes' })
    routes.focus()
    await user.keyboard('{Enter}')
    expect(await screen.findByTestId('routes-panel')).toBeInTheDocument()
  })
})

describe('operator console UI (live/operational default)', () => {
  it('defaults to live empty state without mock recover path', async () => {
    vi.stubGlobal('location', { ...window.location, search: '' })
    render(<App />)
    expect(await screen.findByTestId('mode-banner')).toHaveTextContent('LIVE')
    expect(screen.getByTestId('public-hostname')).toHaveTextContent('swarm.splitsignal.ai')
    expect(screen.getByTestId('live-no-fixture-mutate')).toBeInTheDocument()
    expect(screen.queryByTestId('expand-mission')).not.toBeInTheDocument()
    expect(screen.queryByText(/Recover with mock fixtures/i)).not.toBeInTheDocument()
  })

  it('renders live mission picker artifacts with content hash', async () => {
    vi.stubGlobal('location', {
      ...window.location,
      search: '?mode=live&baseUrl=http://127.0.0.1:9&missionId=msn_live_shared',
      href: 'http://127.0.0.1:43127/?mode=live&baseUrl=http://127.0.0.1:9&missionId=msn_live_shared',
    })
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input)
        if (url.endsWith('/health/ready')) {
          return new Response(JSON.stringify({ status: 'ready' }), { status: 200 })
        }
        if (url.endsWith('/v1/capacity')) {
          return new Response(JSON.stringify({ buckets: [], mock_vs_live: 'live' }), { status: 200 })
        }
        if (url.endsWith('/v1/missions')) {
          return new Response(
            JSON.stringify({
              missions: [
                {
                  mission_id: 'msn_live_shared',
                  objective: 'TH-05 live UI',
                  status: 'planning',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/artifacts')) {
          return new Response(
            JSON.stringify({
              artifacts: [
                {
                  artifact_id: 'art_ui',
                  kind: 'result',
                  content_hash: 'hash_ui_proof',
                  summary: 'ui proof',
                },
              ],
            }),
            { status: 200 },
          )
        }
        if (url.includes('/graph')) {
          return new Response(JSON.stringify({ tasks: [] }), { status: 200 })
        }
        if (url.includes('/events') || url.endsWith('/v1/routes') || url.endsWith('/v1/workers') || url.endsWith('/v1/projects')) {
          return new Response(JSON.stringify({ items: [], routes: [], workers: [], projects: [] }), {
            status: 200,
          })
        }
        if (url.includes('/v1/missions/msn_live_shared')) {
          return new Response(
            JSON.stringify({
              mission: {
                id: 'msn_live_shared',
                objective: 'TH-05 live UI',
                status: 'planning',
                revision: 1,
              },
            }),
            { status: 200 },
          )
        }
        return new Response('missing', { status: 404 })
      }),
    )
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByTestId('mode-banner')).toHaveTextContent('LIVE')
    expect(screen.getByTestId('mission-panel')).toHaveTextContent('msn_live_shared')
    expect(screen.getByTestId('mission-picker')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Artifacts' }))
    expect(await screen.findByTestId('artifact-hash-art_ui')).toHaveTextContent('hash_ui_proof')
  })
})
