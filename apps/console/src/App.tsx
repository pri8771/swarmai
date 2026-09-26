import { useEffect, useState } from 'react'
import {
  cancelLiveWorkerLease,
  emptyLiveSnapshot,
  loadSnapshot,
  resolveConsoleLoadOpts,
  resolveLiveApproval,
  scrubSecrets,
} from './api/client'
import type { ConsoleSnapshot, GoalRow } from './api/types'
import { GoalsPanel } from './components/GoalsPanel'
import { OpsPanel } from './components/OpsPanel'
import { Panel } from './components/Panel'
import { StatusBadge } from './components/StatusBadge'
import {
  contractMission,
  expandMission,
  interruptStream,
} from './data/fixtures'
import './App.css'

type Tab =
  | 'goals'
  | 'mission'
  | 'projects'
  | 'history'
  | 'artifacts'
  | 'routes'
  | 'capacity'
  | 'workers'
  | 'profiles'
  | 'approvals'
  | 'events'
  | 'ops'

export default function App() {
  const [snap, setSnap] = useState<ConsoleSnapshot | null>(null)
  const [tab, setTab] = useState<Tab>('goals')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadOpts, setLoadOpts] = useState(() => resolveConsoleLoadOpts())
  const [controlBusy, setControlBusy] = useState<string | null>(null)
  const [controlNote, setControlNote] = useState<string | null>(null)

  const reload = (next?: { missionId?: string; goalId?: string }) => {
    const opts = resolveConsoleLoadOpts()
    if (next?.missionId) {
      opts.missionId = next.missionId
      if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        url.searchParams.set('missionId', next.missionId)
        window.history.replaceState({}, '', url.toString())
      }
    }
    if (next?.goalId) {
      opts.goalId = next.goalId
      if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        url.searchParams.set('goalId', next.goalId)
        window.history.replaceState({}, '', url.toString())
      }
    }
    setLoadOpts(opts)
    setLoading(true)
    setError(null)
    loadSnapshot(opts)
      .then((s) => {
        setSnap(s)
        setError(null)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : 'load_failed')
        setSnap(null)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    const opts = resolveConsoleLoadOpts()
    setLoadOpts(opts)
    loadSnapshot(opts)
      .then((s) => {
        if (!cancelled) {
          setSnap(s)
          setError(null)
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'load_failed')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="shell" data-testid="loading">
        <p>Loading console snapshot…</p>
      </div>
    )
  }

  if (error || !snap) {
    return (
      <div className="shell" data-testid="error-state">
        <p>Console failed to load: {error ?? 'empty'}</p>
        <button type="button" data-testid="retry-load" onClick={() => reload()}>
          Retry
        </button>
        <p className="muted" data-testid="error-no-mock-recover">
          Operational console does not fall back to mock fixtures. Use ?mode=mock only for
          isolated fixture UI.
        </p>
      </div>
    )
  }

  const fixtureControls = snap.mode === 'mock'
  const tabs: { id: Tab; label: string }[] = [
    { id: 'goals', label: 'Goals' },
    { id: 'mission', label: 'Mission' },
    { id: 'projects', label: 'Projects' },
    { id: 'history', label: 'History' },
    { id: 'artifacts', label: 'Artifacts' },
    { id: 'routes', label: 'Routes' },
    { id: 'capacity', label: 'Capacity' },
    { id: 'workers', label: 'Workers' },
    { id: 'profiles', label: 'Profiles' },
    { id: 'approvals', label: 'Approvals' },
    { id: 'events', label: 'Events' },
    { id: 'ops', label: 'Ops' },
  ]

  return (
    <div className="shell">
      <header className="top">
        <div>
          <p className="brand">SwarmAI Console</p>
          <h1>Goal pursuit</h1>
          <p className="lede">
            Create durable goals, set agents and envelopes, pursue through missions, interrupt or
            redirect, and inspect why the next action was chosen — same contracts as the API/SDK.
          </p>
          <p className="muted" data-testid="public-hostname">
            Public hostname: <code>{snap.hostnamePublic}</code>
            {snap.serverReady === true ? ' · server ready' : null}
            {snap.serverReady === false ? ' · server not ready' : null}
            {loadOpts.baseUrl ? (
              <>
                {' '}
                · API <code>{loadOpts.baseUrl}</code>
              </>
            ) : null}
          </p>
        </div>
        <div className="mode-pill" data-testid="mode-banner">
          <strong>{snap.mode.toUpperCase()}</strong>
          <span>{scrubSecrets(snap.mockVsLive)}</span>
        </div>
      </header>

      {snap.mode === 'live' && (snap.history.length > 0 || snap.goals.length > 0) ? (
        <div className="actions" data-testid="mission-picker">
          {snap.history.length > 0 ? (
            <label htmlFor="mission-select">
              Focus mission{' '}
              <select
                id="mission-select"
                data-testid="mission-select"
                value={snap.mission.missionId}
                onChange={(e) => reload({ missionId: e.target.value })}
              >
                {snap.history.map((h) => (
                  <option key={h.missionId} value={h.missionId}>
                    {h.missionId.slice(0, 12)}… · {h.status} · {h.goal.slice(0, 48)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <button type="button" data-testid="refresh-live" onClick={() => reload()}>
            Refresh
          </button>
        </div>
      ) : null}

      <nav className="tabs" aria-label="Console sections">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? 'tab active' : 'tab'}
            aria-current={tab === t.id ? 'page' : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {snap.errors.length > 0 ? (
        <div className="banner-error" role="alert" data-testid="error-banner">
          {snap.errors.map((e) => (
            <p key={e}>{e}</p>
          ))}
        </div>
      ) : null}

      {tab === 'goals' ? (
        <GoalsPanel
          snap={snap}
          loadOpts={loadOpts}
          onSelectGoal={(goalId) => {
            setSnap({ ...snap, selectedGoalId: goalId })
            if (snap.mode === 'live') {
              reload({ goalId })
            }
          }}
          onGoalsChanged={(goals: GoalRow[], selectedGoalId) => {
            setSnap({ ...snap, goals, selectedGoalId })
          }}
          onPursuitStarted={(goal, missionId) => {
            setSnap({
              ...snap,
              goals: [goal, ...snap.goals.filter((g) => g.id !== goal.id)],
              selectedGoalId: goal.id,
            })
            if (snap.mode === 'live') {
              reload({ missionId, goalId: goal.id })
              if (missionId) setTab('mission')
            }
          }}
        />
      ) : null}

      {tab === 'mission' ? (
        <Panel
          title="Mission graph & activity"
          subtitle={`${snap.mission.missionId} · rev ${snap.mission.revision} · ${snap.mission.status}`}
          testId="mission-panel"
        >
          <p className="objective">{snap.mission.objective}</p>
          <dl className="metrics">
            <div>
              <dt>Planning roles</dt>
              <dd>{snap.mission.planningRoles.join(', ') || '—'}</dd>
            </div>
            <div>
              <dt>Logical agents</dt>
              <dd>{snap.mission.logicalAgents}</dd>
            </div>
            <div>
              <dt>Busy workers</dt>
              <dd>{snap.mission.busyWorkers}</dd>
            </div>
            <div>
              <dt>In-flight inference</dt>
              <dd>{snap.mission.inFlightInference}</dd>
            </div>
          </dl>
          {fixtureControls ? (
            <div className="actions">
              <button
                type="button"
                data-testid="expand-mission"
                onClick={() => setSnap(expandMission(snap))}
              >
                Expand (spawn)
              </button>
              <button
                type="button"
                data-testid="contract-mission"
                onClick={() => setSnap(contractMission(snap))}
              >
                Contract
              </button>
            </div>
          ) : (
            <p className="muted" data-testid="live-no-fixture-mutate">
              Expand/Contract are fixture-only controls. Live mode reflects API state (
              {loadOpts.baseUrl ?? 'no baseUrl'}).
            </p>
          )}
          <table className="grid">
            <thead>
              <tr>
                <th>Task</th>
                <th>Role</th>
                <th>Status</th>
                <th>Waiting / unblock</th>
              </tr>
            </thead>
            <tbody>
              {snap.mission.tasks.map((t) => (
                <tr key={t.id} data-testid={`task-row-${t.id}`}>
                  <td>
                    <code>{t.id}</code>
                    <div>{t.objective}</div>
                  </td>
                  <td>{t.roleHint ?? '—'}</td>
                  <td>
                    <StatusBadge kind="generic" value={t.status} />
                  </td>
                  <td>
                    {t.waitingReason ? (
                      <>
                        <div>{t.waitingReason}</div>
                        <div className="muted">Unblock: {t.unblockEvent}</div>
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.mission.tasks.length === 0 ? (
            <p data-testid="empty-tasks">No tasks in graph.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'projects' ? (
        <Panel
          title="Projects & configuration"
          subtitle="Durable workspace settings — secrets never stored"
          testId="projects-panel"
        >
          <table className="grid">
            <thead>
              <tr>
                <th>Project</th>
                <th>Repo</th>
                <th>Paid</th>
                <th>Tools</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {snap.projects.map((p) => (
                <tr key={p.projectId} data-testid={`project-${p.projectId}`}>
                  <td>
                    <code>{p.projectId}</code>
                    <div>{p.name}</div>
                  </td>
                  <td>
                    <code>{p.repoPath}</code>
                  </td>
                  <td>{p.allowPaid ? 'yes' : 'no'}</td>
                  <td>{p.allowedTools.join(', ')}</td>
                  <td>{p.updatedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.projects.length === 0 ? (
            <p data-testid="empty-projects">No projects configured.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'history' ? (
        <Panel
          title="Mission history"
          subtitle="Reopenable / searchable completed missions"
          testId="history-panel"
        >
          <table className="grid">
            <thead>
              <tr>
                <th>Mission</th>
                <th>Status</th>
                <th>Cost</th>
                <th>Artifacts</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {snap.history.map((h) => (
                <tr key={h.missionId} data-testid={`history-${h.missionId}`}>
                  <td>
                    <code>{h.missionId}</code>
                    <div>{h.goal}</div>
                  </td>
                  <td>
                    <StatusBadge kind="generic" value={h.status} />
                  </td>
                  <td>${h.costUsd.toFixed(2)}</td>
                  <td>{h.artifactCount}</td>
                  <td>{h.tags.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      ) : null}

      {tab === 'artifacts' ? (
        <Panel
          title="Artifacts"
          subtitle="Reports, diffs, and mission outputs"
          testId="artifacts-panel"
        >
          <ul className="timeline" data-testid="artifact-list">
            {snap.artifacts.map((a) => (
              <li key={a.artifactId} data-testid={`artifact-${a.artifactId}`}>
                <code>{a.artifactId}</code> — {a.kind}
                {a.summary ? <div className="muted">{a.summary}</div> : null}
                {a.contentHash ? (
                  <div className="muted" data-testid={`artifact-hash-${a.artifactId}`}>
                    sha256: <code>{a.contentHash}</code>
                    {typeof a.byteLength === 'number' ? ` · ${a.byteLength} bytes` : null}
                  </div>
                ) : null}
                {a.uri ? (
                  <div className="muted">
                    <code>{a.uri}</code>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
          {snap.artifacts.length === 0 ? (
            <p data-testid="empty-artifacts">No artifacts for focused mission.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'routes' ? (
        <Panel title="Routes & providers" subtitle="No greenwashing of retired/unknown/gated" testId="routes-panel">
          <table className="grid">
            <thead>
              <tr>
                <th>Route</th>
                <th>Provider / model</th>
                <th>Availability</th>
                <th>Claims</th>
              </tr>
            </thead>
            <tbody>
              {snap.routes.map((r) => (
                <tr key={r.routeId} data-testid={`route-${r.routeId}`}>
                  <td>
                    <code>{r.routeId}</code>
                  </td>
                  <td>
                    {r.provider} / {r.modelId ?? '—'}
                  </td>
                  <td>
                    <StatusBadge kind="availability" value={r.availability} />
                    <div className="muted">{r.status}</div>
                  </td>
                  <td>{r.capabilityClaims.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.routes.length === 0 ? (
            <p data-testid="empty-routes">No routes configured or observed.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'capacity' ? (
        <Panel
          title="Capacity by actual units"
          subtitle={snap.capacityUnknown ? 'Some remaining values unknown — shown as unknown' : undefined}
          testId="capacity-panel"
        >
          <table className="grid">
            <thead>
              <tr>
                <th>Bucket</th>
                <th>Dimension</th>
                <th>Remaining</th>
                <th>Limit</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {snap.capacity.map((b) => (
                <tr key={b.bucketId} data-testid={`bucket-${b.bucketId}`}>
                  <td>
                    <code>{b.bucketId}</code>
                  </td>
                  <td>{b.dimension}</td>
                  <td data-testid={`remaining-${b.bucketId}`}>
                    {b.remaining === null ? 'unknown' : b.remaining}
                  </td>
                  <td>{b.limit === null ? 'unknown' : b.limit}</td>
                  <td>{b.note ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.capacity.length === 0 ? (
            <p data-testid="empty-capacity">Capacity unknown until accounts are configured and probed.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'workers' ? (
        <Panel
          title="Workers"
          subtitle="Stale heartbeats called out; cancel active leases via API"
          testId="workers-panel"
        >
          {controlNote ? <p data-testid="worker-control-note">{controlNote}</p> : null}
          <table className="grid">
            <thead>
              <tr>
                <th>Worker</th>
                <th>Status</th>
                <th>Gen</th>
                <th>Capacity</th>
                <th>Privacy</th>
                <th>Claimed</th>
                <th>Control</th>
              </tr>
            </thead>
            <tbody>
              {snap.workers.map((w) => (
                <tr key={w.workerId} data-testid={`worker-${w.workerId}`}>
                  <td>
                    <code>{w.workerId}</code>
                    {w.stale ? <StatusBadge kind="generic" value="stale" /> : null}
                    {w.revoked ? <StatusBadge kind="generic" value="revoked" /> : null}
                  </td>
                  <td>
                    <StatusBadge kind="generic" value={w.status} />
                  </td>
                  <td>{w.generation}</td>
                  <td>{w.capacity}</td>
                  <td>{w.privacy.join(', ')}</td>
                  <td>{w.claimed ?? '—'}</td>
                  <td>
                    {(w.activeLeases ?? []).length === 0 ? (
                      <span className="muted">—</span>
                    ) : (
                      (w.activeLeases ?? []).map((leaseId) => (
                        <button
                          key={leaseId}
                          type="button"
                          data-testid={`cancel-lease-${leaseId}`}
                          disabled={!!controlBusy || snap.mode !== 'live' || !loadOpts.baseUrl}
                          onClick={() => {
                            if (!loadOpts.baseUrl) return
                            setControlBusy(leaseId)
                            setControlNote(null)
                            void cancelLiveWorkerLease({
                              baseUrl: loadOpts.baseUrl,
                              token: loadOpts.token,
                              leaseId,
                              reason: 'console_operator_cancel',
                            })
                              .then((res) => {
                                setControlNote(`Cancelled lease ${res.lease_id} → ${res.state}`)
                                reload()
                              })
                              .catch((e: unknown) => {
                                setControlNote(
                                  e instanceof Error ? e.message : 'cancel_lease_failed',
                                )
                              })
                              .finally(() => setControlBusy(null))
                          }}
                        >
                          {controlBusy === leaseId ? 'Cancelling…' : `Cancel ${leaseId.slice(0, 10)}…`}
                        </button>
                      ))
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.workers.length === 0 ? (
            <p data-testid="empty-workers">No workers enrolled.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'profiles' ? (
        <Panel title="Task / size profiles" subtitle="Qualified vs provisional evidence" testId="profiles-panel">
          <table className="grid">
            <thead>
              <tr>
                <th>Key</th>
                <th>Family / size</th>
                <th>State</th>
                <th>Wilson LCB</th>
                <th>Distinct cases</th>
              </tr>
            </thead>
            <tbody>
              {snap.profiles.map((p) => (
                <tr key={p.key} data-testid={`profile-${p.key}`}>
                  <td>
                    <code>{p.key}</code>
                  </td>
                  <td>
                    {p.taskFamily} / {p.sizeBand}
                  </td>
                  <td>
                    <StatusBadge kind="profile" value={p.state} />
                  </td>
                  <td>{p.wilsonLower ?? '—'}</td>
                  <td>{p.distinctCases ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {snap.profiles.length === 0 ? (
            <p data-testid="empty-profiles">No profiles measured yet.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'approvals' ? (
        <Panel
          title="Approvals"
          subtitle="Resolve via POST /v1/approvals/{id}/resolve (same as SDK)"
          testId="approvals-panel"
        >
          {controlNote && tab === 'approvals' ? (
            <p data-testid="approval-control-note">{controlNote}</p>
          ) : null}
          {snap.approvals.map((a) => (
            <article key={a.id} className="approval" data-testid={`approval-${a.id}`}>
              <h3>
                <code>{a.id}</code> — {a.operation}
              </h3>
              <p>
                Destination: <code>{a.destination}</code>
              </p>
              <p>
                Payload hash: <code>{a.payloadHash}</code>
              </p>
              <pre data-testid="approval-payload">{JSON.stringify(a.payloadPreview, null, 2)}</pre>
              <div className="actions">
                <button
                  type="button"
                  data-testid={`approval-accept-${a.id}`}
                  disabled={
                    !!controlBusy ||
                    !!a.revokedAt ||
                    snap.mode !== 'live' ||
                    !loadOpts.baseUrl
                  }
                  onClick={() => {
                    if (!loadOpts.baseUrl) return
                    setControlBusy(a.id)
                    setControlNote(null)
                    void resolveLiveApproval({
                      baseUrl: loadOpts.baseUrl,
                      token: loadOpts.token,
                      approvalId: a.id,
                      accept: true,
                    })
                      .then(() => {
                        setControlNote(`Accepted ${a.id}`)
                        reload()
                      })
                      .catch((e: unknown) => {
                        setControlNote(e instanceof Error ? e.message : 'resolve_failed')
                      })
                      .finally(() => setControlBusy(null))
                  }}
                >
                  Accept
                </button>
                <button
                  type="button"
                  data-testid={`approval-reject-${a.id}`}
                  disabled={
                    !!controlBusy ||
                    !!a.revokedAt ||
                    snap.mode !== 'live' ||
                    !loadOpts.baseUrl
                  }
                  onClick={() => {
                    if (!loadOpts.baseUrl) return
                    setControlBusy(a.id)
                    setControlNote(null)
                    void resolveLiveApproval({
                      baseUrl: loadOpts.baseUrl,
                      token: loadOpts.token,
                      approvalId: a.id,
                      accept: false,
                    })
                      .then(() => {
                        setControlNote(`Rejected ${a.id}`)
                        reload()
                      })
                      .catch((e: unknown) => {
                        setControlNote(e instanceof Error ? e.message : 'resolve_failed')
                      })
                      .finally(() => setControlBusy(null))
                  }}
                >
                  Reject
                </button>
              </div>
            </article>
          ))}
          {snap.approvals.length === 0 ? (
            <p data-testid="empty-approvals">No pending approvals.</p>
          ) : null}
        </Panel>
      ) : null}

      {tab === 'events' ? (
        <Panel title="Event timeline" subtitle="At-least-once; reconnect recovers missed state" testId="events-panel">
          {fixtureControls ? (
            <div className="actions">
              <button
                type="button"
                data-testid="interrupt-stream"
                onClick={() => setSnap(interruptStream(snap))}
              >
                Simulate stream interrupt
              </button>
            </div>
          ) : null}
          {snap.streamInterrupted ? (
            <p data-testid="stream-interrupted">Stream interrupted — use continuation cursor.</p>
          ) : null}
          <ol className="timeline">
            {snap.events.map((e) => (
              <li key={e.id}>
                <code>{e.type}</code> — {e.summary}
              </li>
            ))}
          </ol>
        </Panel>
      ) : null}

      {tab === 'ops' ? (
        <OpsPanel
          mode={snap.mode}
          baseUrl={loadOpts.baseUrl}
          token={loadOpts.token}
          workers={snap.workers}
        />
      ) : null}
    </div>
  )
}

/** Test helper export — empty live baseline without fixtures. */
export { emptyLiveSnapshot }
