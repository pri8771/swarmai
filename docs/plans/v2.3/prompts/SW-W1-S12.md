# SW-W1-S12 — Console: Ops tab (read-only) + worker drain/revoke parity (V20-E09)

Copy this whole file into a fresh Cursor session opened on the **swarmai** repository. Follow it top to bottom. It is self-contained: do not read other plans to decide what to do.

| Field | Value |
|---|---|
| Session ID | `SW-W1-S12` |
| Repository | `pri8771/swarmai` (GitHub remote `origin`; **public** repo) |
| Base branch | `cursor/sw-v23-integration-460c` — always the **current** `origin/cursor/sw-v23-integration-460c` (plan baseline `dev` @ `8e1c0fde`) |
| Your branch | `cursor/v20-w1-s12-console-ops` |
| Branch-suffix rule | If your environment forces a suffix (for example `-460c`), append it **once** to *your* branch and write the exact final name in the handoff. Never add a suffix to `cursor/sw-v23-integration-460c`: it already ends in `-460c`. |
| PR target | `cursor/sw-v23-integration-460c` — **draft** PR. Never `dev`, never `main`. |
| Wave | 1 |
| Depends on | none |
| Handoff file | `docs/v2.3/sessions/SW-W1-S12.md` |
| Independent reviewer | Codex (owner decision D2). You never accept your own work. |
| Plan | `docs/plans/v2.3/PLAN.md`; owner preflight `docs/plans/v2.3/OWNER_PREFLIGHT.md`; decisions `docs/swarm-mvp/DECISIONS.md` |

## 0. Hard rules (read twice)
1. Edit **only** the files listed in “Files you own” plus your handoff file. If another file must change, do not change it: write the exact change under “Needs other owner” in the handoff.
2. Never push to, or merge into, `main`, `dev` or `cursor/sw-v23-integration-460c`. Never merge any PR, never force-push, never rewrite history, never delete branches. Only the wave MERGE prompts (`SW-MERGE-*`) push to `cursor/sw-v23-integration-460c`.
3. Zero spend: no real model/provider calls, no paid APIs, no account creation, no deploys. `SWARM_ALLOW_PAID` stays `false`. Tests use fakes only.
4. Never commit or print secrets, tokens, `.env` files, customer data or raw logs. Test tokens are fake literals such as `atk_policy_demo`. Check environment variables only with `test -n "$NAME"`.
5. Passing tests are *not* acceptance. Never write “accepted”, “complete”, “released” or “V2.3 done”. Use “implemented” and “tested”.
6. `src/swarm/contracts/v23.py`, `src/swarm/db/models.py` and `migrations/` belong to SW-W0-S2. Import from them; never edit them (unless you *are* SW-W0-S2).
7. Do not edit `.github/workflows/`, `pyproject.toml`, `uv.lock`, `package.json` or lockfiles.
8. If a step can be read two ways, choose the reading that changes fewer lines inside your own files, and write the choice under “Decisions” in the handoff.

## 1. Setup
```bash
git status --porcelain            # must print nothing; otherwise STOP (S1)
git fetch origin cursor/sw-v23-integration-460c
git ls-remote --exit-code origin refs/heads/cursor/sw-v23-integration-460c >/dev/null && echo INTEG_OK || echo INTEG_MISSING
```
If it prints `INTEG_MISSING`, STOP (S2): SW-W0-S1 or the executor creates it.
```bash
git checkout -b cursor/v20-w1-s12-console-ops origin/cursor/sw-v23-integration-460c
git log -1 --format='%H %s'       # record this SHA in the handoff as 'base'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh   # then: export PATH=$HOME/.local/bin:$PATH
uv sync
git clean -fdX -- var/
```

## 2. Dependency and environment check
This session has **no dependencies**. Go to Step 1.

This session needs **no** secrets or environment variables.

## 3. Files you own (the ONLY files you may create or modify)
- `apps/console/src/App.tsx` — modify
- `apps/console/src/api/client.ts` — modify
- `apps/console/src/api/types.ts` — modify
- `apps/console/src/data/fixtures.ts` — modify
- `apps/console/src/components/OpsPanel.tsx` — create
- `apps/console/src/components/WorkerControls.tsx` — create
- `apps/console/src/ops.test.tsx` — create
- `docs/v2.3/sessions/SW-W1-S12.md` — create (your handoff)

## 4. Do NOT touch
- Any file not listed in section 3 (in particular: `src/swarm/api/app.py`, `src/swarm/api/store.py`, `src/swarm/cli.py`, `src/swarm/db/models.py`, `migrations/`, `docs/agents/*`, `docs/plans/v2.3/*`, `CHANGELOG.md`, `README.md`, `.github/`, unless listed above).
- The `inference_server` repository: read-only, and only through the commands in section 5.
- The branches `main`, `dev`, `cursor/sw-v23-integration-460c`, `cursor/v23-plan-460c`, and any other session's branch.
- Generated files that tests rewrite: `schemas/v1/*`, `docs/evidence/fix-004/*`, `var/*` — always restore them before committing (section 6).

## 5. Steps
**Goal.** Implement V20-E09 console parity for V2.3 operations.
- Add a read-only **Ops** tab showing the scheduler queues and ops events.
- Add worker **drain / revoke** controls that call the authenticated API, which is the action boundary.

The server endpoints come from SW-W3-S1: `GET /v1/scheduler/queues`, and `POST /v1/workers/{id}/drain` and `/revoke`. They may not exist yet, so the UI must handle a **404 honestly**: show "not available", and never fake data. Live mode never falls back to fixtures; mock mode (`?mode=mock`) uses `MOCK_OPS`.

**API shapes this UI expects.** SW-W3-S1 implements exactly these:
- `GET /v1/ops/events` → `{"events": [{"event_id","kind","component","project_id","trace_id","at",...}]}`. This already exists.
- `GET /v1/scheduler/queues` → `{"projects": [{"project_id","weight","credit","running","max_concurrency","paused"}]}`.
- `POST /v1/workers/{worker_id}/drain` and `/revoke`, body `{"reason": str}` → `{"worker_id","drain_state"}`.

The code below was run against `dev @ 8e1c0fde`: `npm run lint` shows 0 errors and only the 2 existing warnings, `npm run test` gives 26 passed (5 new), and `npm run build` succeeds. Work inside `apps/console`. **No Python changes.**

### Step 1 — `apps/console/src/api/types.ts` (append at the very end of the file, exactly)
```ts

export interface OpsEventRow {
  eventId: string
  kind: string
  component: string
  projectId: string | null
  traceId: string | null
  at: string
}

export interface SchedulerQueueRow {
  projectId: string
  weight: number
  credit: number
  running: number
  maxConcurrency: number
  paused: boolean
}

export interface OpsView {
  mode: 'mock' | 'live'
  events: OpsEventRow[]
  queues: SchedulerQueueRow[]
  /** False when the server has no /v1/scheduler/queues (404) — shown honestly, never faked. */
  queuesAvailable: boolean
  errors: string[]
}
```

### Step 2 — `apps/console/src/api/client.ts`
(a) Replace the import block at the top of the file. Find exactly:
```ts
  MissionTask,
  PursuitStatus,
} from './types'
import { MOCK_SNAPSHOT } from '../data/fixtures'
```
and replace it with:
```ts
  MissionTask,
  OpsEventRow,
  OpsView,
  PursuitStatus,
  SchedulerQueueRow,
} from './types'
import { MOCK_OPS, MOCK_SNAPSHOT } from '../data/fixtures'
```
(b) Append the following at the very end of the file, exactly. It reuses the existing private helpers `fetchJson`, `mutateJson` and `assertNoSecretsInBundle`; do not change those helpers.
```ts

function opsEventFromApi(raw: Record<string, unknown>): OpsEventRow {
  return {
    eventId: String(raw.event_id ?? ''),
    kind: String(raw.kind ?? ''),
    component: String(raw.component ?? ''),
    projectId: raw.project_id == null ? null : String(raw.project_id),
    traceId: raw.trace_id == null ? null : String(raw.trace_id),
    at: String(raw.at ?? ''),
  }
}

function queueFromApi(raw: Record<string, unknown>): SchedulerQueueRow {
  return {
    projectId: String(raw.project_id ?? ''),
    weight: Number(raw.weight ?? 0),
    credit: Number(raw.credit ?? 0),
    running: Number(raw.running ?? 0),
    maxConcurrency: Number(raw.max_concurrency ?? 0),
    paused: raw.paused === true,
  }
}

/** Ops tab data. Mock → MOCK_OPS; live → GET /v1/ops/events + /v1/scheduler/queues (never fixtures). */
export async function loadOps(opts: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}): Promise<OpsView> {
  if (opts.mode === 'mock') {
    const view = structuredClone(MOCK_OPS)
    assertNoSecretsInBundle(view)
    return view
  }
  const view: OpsView = { mode: 'live', events: [], queues: [], queuesAvailable: false, errors: [] }
  if (!opts.baseUrl) {
    view.errors.push('ops_requires_baseUrl')
    return view
  }
  const base = opts.baseUrl.replace(/\/$/, '')
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  try {
    const events = await fetchJson(`${base}/v1/ops/events`, headers)
    if (events.ok) {
      const rows = (events.body as { events?: Array<Record<string, unknown>> }).events ?? []
      view.events = rows.map(opsEventFromApi)
    } else {
      view.errors.push(`ops_events_http_${events.status}`)
    }
    const queues = await fetchJson(`${base}/v1/scheduler/queues`, headers)
    if (queues.ok) {
      const rows = (queues.body as { projects?: Array<Record<string, unknown>> }).projects ?? []
      view.queues = rows.map(queueFromApi)
      view.queuesAvailable = true
    } else if (queues.status !== 404) {
      view.errors.push(`scheduler_queues_http_${queues.status}`)
    }
  } catch (e: unknown) {
    view.errors.push(e instanceof Error ? e.message : 'ops_load_failed')
  }
  return view
}

/** Live: POST /v1/workers/{id}/drain | /revoke. A 404 means the server lacks the route. */
export async function workerControl(opts: {
  baseUrl: string
  token?: string
  workerId: string
  action: 'drain' | 'revoke'
  reason?: string
}): Promise<{ available: boolean; drainState: string | null }> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  try {
    const payload = await mutateJson(
      `${base}/v1/workers/${encodeURIComponent(opts.workerId)}/${opts.action}`,
      headers,
      'POST',
      { reason: opts.reason ?? `operator_${opts.action}` },
    )
    return { available: true, drainState: String(payload.drain_state ?? 'unknown') }
  } catch (e: unknown) {
    if (e instanceof Error && e.message === 'api_error_404') {
      return { available: false, drainState: null }
    }
    throw e
  }
}
```

### Step 3 — `apps/console/src/data/fixtures.ts`
(a) Change the import line `import type { ConsoleSnapshot } from '../api/types'` to:
```ts
import type { ConsoleSnapshot, OpsView } from '../api/types'
```
(b) Append at the very end of the file, exactly. **Do not** change `MOCK_SNAPSHOT`.
```ts

/** Deterministic Ops tab fixture — mock mode only. */
export const MOCK_OPS: OpsView = {
  mode: 'mock',
  events: [
    {
      eventId: 'oev_mock_1',
      kind: 'scheduler.decision',
      component: 'scheduler',
      projectId: 'proj_demo',
      traceId: 'tr_mock_1',
      at: '2026-09-01T00:00:00+00:00',
    },
    {
      eventId: 'oev_mock_2',
      kind: 'attempt.started',
      component: 'controller',
      projectId: 'proj_demo',
      traceId: 'tr_mock_1',
      at: '2026-09-01T00:00:01+00:00',
    },
  ],
  queues: [
    {
      projectId: 'proj_demo',
      weight: 1,
      credit: 0.25,
      running: 1,
      maxConcurrency: 4,
      paused: false,
    },
  ],
  queuesAvailable: true,
  errors: [],
}
```

### Step 4 — `apps/console/src/components/WorkerControls.tsx` (create, exactly)
```tsx
import { useState } from 'react'
import { workerControl } from '../api/client'
import type { WorkerRow } from '../api/types'

export function WorkerControls({
  workers,
  mode,
  baseUrl,
  token,
}: {
  workers: WorkerRow[]
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}) {
  const [busy, setBusy] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)
  const disabled = !!busy || mode !== 'live' || !baseUrl

  const run = (workerId: string, action: 'drain' | 'revoke') => {
    if (!baseUrl) return
    setBusy(`${action}:${workerId}`)
    setNote(null)
    void workerControl({ baseUrl, token, workerId, action, reason: `console_operator_${action}` })
      .then((res) => {
        setNote(
          res.available
            ? `${workerId} → ${res.drainState}`
            : `${action === 'drain' ? 'Drain' : 'Revoke'} not available on this server`,
        )
      })
      .catch((e: unknown) => setNote(e instanceof Error ? e.message : `${action}_failed`))
      .finally(() => setBusy(null))
  }

  return (
    <div data-testid="worker-controls">
      <h3>Worker drain / revoke</h3>
      {mode !== 'live' ? (
        <p className="muted" data-testid="worker-controls-mock">
          Fixture mode: controls disabled. Live controls call the authenticated API.
        </p>
      ) : null}
      {note ? <p data-testid="worker-controls-note">{note}</p> : null}
      <table className="grid">
        <thead>
          <tr>
            <th>Worker</th>
            <th>Status</th>
            <th>Control</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((w) => (
            <tr key={w.workerId} data-testid={`ops-worker-${w.workerId}`}>
              <td>
                <code>{w.workerId}</code>
              </td>
              <td>{w.revoked ? 'revoked' : w.status}</td>
              <td>
                <button
                  type="button"
                  data-testid={`drain-${w.workerId}`}
                  disabled={disabled || w.revoked}
                  onClick={() => run(w.workerId, 'drain')}
                >
                  Drain
                </button>{' '}
                <button
                  type="button"
                  data-testid={`revoke-${w.workerId}`}
                  disabled={disabled || w.revoked}
                  onClick={() => run(w.workerId, 'revoke')}
                >
                  Revoke
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {workers.length === 0 ? <p data-testid="ops-no-workers">No workers enrolled.</p> : null}
    </div>
  )
}
```

### Step 5 — `apps/console/src/components/OpsPanel.tsx` (create, exactly)
```tsx
import { useEffect, useState } from 'react'
import { loadOps } from '../api/client'
import type { OpsView, WorkerRow } from '../api/types'
import { Panel } from './Panel'
import { WorkerControls } from './WorkerControls'

export function OpsPanel({
  mode,
  baseUrl,
  token,
  workers,
}: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
  workers: WorkerRow[]
}) {
  const [view, setView] = useState<OpsView | null>(null)

  useEffect(() => {
    let cancelled = false
    void loadOps({ mode, baseUrl, token }).then((v) => {
      if (!cancelled) setView(v)
    })
    return () => {
      cancelled = true
    }
  }, [mode, baseUrl, token])

  return (
    <Panel
      title="Operations"
      subtitle="Read-only scheduler and ops events; mutations only via the authenticated API"
      testId="ops-panel"
    >
      {view === null ? <p data-testid="ops-loading">Loading ops…</p> : null}
      {view && view.errors.length > 0 ? (
        <div className="banner-error" role="alert" data-testid="ops-errors">
          {view.errors.map((e) => (
            <p key={e}>{e}</p>
          ))}
        </div>
      ) : null}
      {view ? (
        <>
          <h3>Scheduler queues</h3>
          {view.queuesAvailable ? (
            <table className="grid" data-testid="ops-queues">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Weight</th>
                  <th>Credit</th>
                  <th>Running / max</th>
                  <th>Paused</th>
                </tr>
              </thead>
              <tbody>
                {view.queues.map((q) => (
                  <tr key={q.projectId} data-testid={`ops-queue-${q.projectId}`}>
                    <td>
                      <code>{q.projectId}</code>
                    </td>
                    <td>{q.weight}</td>
                    <td>{q.credit.toFixed(3)}</td>
                    <td>
                      {q.running} / {q.maxConcurrency}
                    </td>
                    <td>{q.paused ? 'yes' : 'no'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="muted" data-testid="ops-queues-unavailable">
              Scheduler queues not available on this server.
            </p>
          )}
          <h3>Ops events</h3>
          <table className="grid" data-testid="ops-events">
            <thead>
              <tr>
                <th>At</th>
                <th>Kind</th>
                <th>Component</th>
                <th>Project</th>
                <th>Trace</th>
              </tr>
            </thead>
            <tbody>
              {view.events.map((e) => (
                <tr key={e.eventId} data-testid={`ops-event-${e.eventId}`}>
                  <td>{e.at}</td>
                  <td>
                    <code>{e.kind}</code>
                  </td>
                  <td>{e.component}</td>
                  <td>{e.projectId ?? '—'}</td>
                  <td>{e.traceId ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {view.events.length === 0 ? <p data-testid="ops-no-events">No ops events.</p> : null}
        </>
      ) : null}
      <WorkerControls workers={workers} mode={mode} baseUrl={baseUrl} token={token} />
    </Panel>
  )
}
```

### Step 6 — `apps/console/src/App.tsx` (four small edits; change nothing else)
1. After the line `import { GoalsPanel } from './components/GoalsPanel'` add:
   ```tsx
   import { OpsPanel } from './components/OpsPanel'
   ```
2. In `type Tab = …`, after the line `  | 'events'` add the line `  | 'ops'`.
3. In the `tabs` array, after `    { id: 'events', label: 'Events' },` add:
   ```tsx
       { id: 'ops', label: 'Ops' },
   ```
4. Find the **last** `      ) : null}` in the component, the one that closes the `tab === 'events'` block just before `    </div>`. After it, insert:
   ```tsx

         {tab === 'ops' ? (
           <OpsPanel
             mode={snap.mode}
             baseUrl={loadOpts.baseUrl}
             token={loadOpts.token}
             workers={snap.workers}
           />
         ) : null}
   ```

### Step 7 — `apps/console/src/ops.test.tsx` (create, exactly)
```tsx
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
```

### Step 8 — run
```bash
cd apps/console && npm ci && npm run lint && npm run test && npm run build && cd ../..
```
`apps/console/dist/` is git-ignored; do not commit it.

### Section-5 acceptance
- [ ] An **Ops** tab exists. Mock mode shows the `MOCK_OPS` events and queue and a "controls disabled" note.
- [ ] Live mode reads `/v1/ops/events` and `/v1/scheduler/queues`; a 404 on queues shows "Scheduler queues not available on this server"; fixture rows never appear in live mode.
- [ ] Drain and revoke POST to `/v1/workers/{id}/drain|revoke` with the bearer token; success shows `wk → <drain_state>`, and a 404 shows "… not available on this server".
- [ ] The existing `src/console.test.tsx` passes unchanged; lint shows no errors.

## 6. Verify (run exactly; all must pass)
```bash
git clean -fdX -- var/            # F-15: stale runtime state breaks re-runs
cd apps/console
npm ci
npm run lint      # warnings allowed, errors not
npm run test
npm run build
cd ../..
uv run ruff check .   # sanity: python untouched

git checkout -- schemas/v1 docs/evidence/fix-004 var   # tests rewrite these tracked files
git status --porcelain            # every path listed must be one of YOUR files
```

### PostgreSQL (for the integration line)
```bash
pg_isready -h 127.0.0.1 || {
  sudo apt-get update && sudo apt-get install -y postgresql && sudo service postgresql start
  sudo -u postgres psql -c "CREATE USER swarm WITH PASSWORD 'swarm' SUPERUSER;" || true
}
```
Run this block before section 6. Section 6 creates your private database and exports `SWARM_DATABASE_URL` for **both** pytest lines; never unset it and never point it at the shared `swarm` database.
If `pg_isready -h 127.0.0.1` still fails after running this block twice, write `integration: SKIPPED (postgres unavailable: <last error line>)` in the handoff and continue. Never claim integration passed without running it.

## 7. Acceptance checklist (tick every box in the handoff)
- [ ] Every step in section 5 done; every acceptance box in section 5 ticked.
- [ ] `npm run lint` (no errors), `npm run test`, `npm run build` pass.
- [ ] No Python file changed.
- [ ] Existing `src/console.test.tsx` still passes unchanged.
- [ ] Mock mode renders the new UI; live mode never falls back to fixtures.
- [ ] `git status --porcelain` lists only files from section 3 + the handoff.
- [ ] No secrets, no network calls beyond section 5, no `accepted`/`complete` claims.
- [ ] The Codex review packet (section 11) is in the PR description and the handoff.

## 8. Commit, push, draft PR
```bash
git checkout -- schemas/v1 docs/evidence/fix-004 var
git add apps/console/src/App.tsx apps/console/src/api/client.ts apps/console/src/api/types.ts apps/console/src/data/fixtures.ts apps/console/src/components/OpsPanel.tsx apps/console/src/components/WorkerControls.tsx apps/console/src/ops.test.tsx docs/v2.3/sessions/SW-W1-S12.md
git status --porcelain            # nothing unexpected staged or left over
git commit -m "feat(console): read-only Ops tab and worker drain/revoke controls via action boundary (E09)" -m "Session: SW-W1-S12. Plan: docs/plans/v2.3/PLAN.md."
git push -u origin cursor/v20-w1-s12-console-ops
gh pr create --draft --base cursor/sw-v23-integration-460c --head cursor/v20-w1-s12-console-ops --title "[SW-W1-S12] Console: Ops tab (read-only) + worker drain/revoke parity (V20-E09)" --body-file docs/v2.3/sessions/SW-W1-S12.md
git ls-remote origin refs/heads/cursor/v20-w1-s12-console-ops   # must print the same SHA as: git rev-parse HEAD
```
If `gh pr create` is refused (read-only `gh`), the environment opens the PR: check that its base is `cursor/sw-v23-integration-460c` and that it is a draft, and put the PR URL (or the compare URL from section 10, step 4) into the handoff.
If push fails for network reasons, retry up to 4 times waiting 4 s, 8 s, 16 s, 32 s; then STOP (S8).
Docs to update: only your handoff file, plus any doc listed in section 3.

## 9. Handoff file (create before committing)
Create `docs/v2.3/sessions/SW-W1-S12.md` with exactly these headings:
```markdown
# SW-W1-S12 handoff
- Branch: <exact branch name>   Base SHA: <from setup>   Head SHA: <git rev-parse HEAD>
- PR: <url, or compare URL>
## Done
<bullet list of what you implemented>
## Verification
<each command from section 6 and its final result line; integration PASSED/SKIPPED(reason)>
## Acceptance
<copy the checkboxes from sections 5 and 7, ticked>
## Decisions
<choices you made under hard rule 8, or 'none'>
## Needs other owner
<files outside your scope that should change, with the exact change; or 'none'>
## Codex review packet
<the block from section 11, filled in>
## Status
implemented + tested (NOT accepted; needs Codex review)
```

## 10. STOP conditions (never wait for a human)
STOP immediately when any of these is true:
- **S1** `git status --porcelain` is not empty before Setup. (Do not commit, stash or discard anything; skip steps 1–4 below and only report.)
- **S2** a dependency check prints `MISSING`.
- **S3** a command in section 6, or a check in section 5, still fails after **2 attempts**. One attempt = one edit to *your own files* followed by re-running the failing command.
- **S4** a “currently reads” / before-block in section 5 does not match the file, or a function named in section 5 does not exist.
- **S5** finishing would require editing a file that is not in section 3.
- **S6** a required environment variable prints `MISSING`.
- **S7** an external gate check (inference_server sync point or approval line) in section 5 fails.
- **S8** `git push` still fails after 4 retries (waits 4 s, 8 s, 16 s, 32 s).

What to do on STOP, in this order:
1. Commit whatever is complete inside your own files: `git add <your files> docs/v2.3/sessions/SW-W1-S12.md` then `git commit -m "WIP(SW-W1-S12): <one-line reason>"`.
2. Write the handoff (section 9) with `## Status` = `BLOCKED: <condition id> <one-line reason>`, and under `## Needs other owner` the exact file, function and change you need. Commit it.
3. Push: `git push -u origin cursor/v20-w1-s12-console-ops` (plus your suffix).
4. Open the draft PR against `cursor/sw-v23-integration-460c` with the title prefix `[BLOCKED]`, or record the compare URL `https://github.com/pri8771/swarmai/compare/cursor/sw-v23-integration-460c...cursor/v20-w1-s12-console-ops?expand=1` in the handoff.
5. End the session with a final message: the condition id, the reason, the branch and the head SHA.
Never work around a STOP by editing other files, weakening tests, or adding `skip`/`xfail`.

If `tests/tools/test_v20_cancel_killbound.py` fails once in the full run and you did not touch `sandbox_runner.py` or that test, re-run the full list once. If it passes, record both result lines in the handoff under Verification and continue; if it fails twice, STOP (S3). (The known race was fixed by SW-FIX-FLAKE; a new failure is worth reporting.)

## 11. Codex review packet (put this in the PR description and in the handoff)
```markdown
### Codex review packet — SW-W1-S12
- PR: <PR URL — fill in after the PR exists>
- Branch: <exact branch name>  Base: origin/cursor/sw-v23-integration-460c @ <base SHA from Setup>
- Head SHA: <output of `git rev-parse HEAD`; must equal `git ls-remote origin refs/heads/<branch>`>
- Diff for review: `git diff <base SHA>...<head SHA>`
- Files to review: `apps/console/src/App.tsx`, `apps/console/src/api/client.ts`, `apps/console/src/api/types.ts`, `apps/console/src/data/fixtures.ts`, `apps/console/src/components/OpsPanel.tsx`, `apps/console/src/components/WorkerControls.tsx`, `apps/console/src/ops.test.tsx`, `docs/v2.3/sessions/SW-W1-S12.md`
- Review focus (AGENTS.md Code Review Rules): cross-tenant/project access; secret disclosure; financial accounting (unknown usage or cost is never zero); unbounded retries; silently changed model behaviour; recovery gaps after a crash/restart; unsupported release claims ("accepted", "complete"). Session-specific: console mutations go only through the action boundary; live mode never falls back to fixtures.
- Checks run: <paste the final result line of every command in section 6>
- Verdict requested: `RECOMMEND_ACCEPT <head SHA>` or `REQUEST_CHANGES` with file:line findings.
```
