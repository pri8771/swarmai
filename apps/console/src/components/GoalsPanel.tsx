/** Goal pursuit panel — create, agents, resources, pursue, interrupt/resume, why-next. */

import { useState } from 'react'
import {
  createLiveGoal,
  startLivePursuit,
  transitionLiveGoal,
} from '../api/client'
import type { ConsoleSnapshot, GoalRow, GoalStatus } from '../api/types'
import { Panel } from './Panel'
import { StatusBadge } from './StatusBadge'

type LoadOpts = {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}

type Props = {
  snap: ConsoleSnapshot
  loadOpts: LoadOpts
  onSelectGoal: (goalId: string) => void
  onGoalsChanged: (goals: GoalRow[], selectedGoalId: string | null) => void
  onPursuitStarted: (goal: GoalRow, missionId?: string) => void
}

function parseCsv(value: string): string[] {
  return value
    .split(/[,;\n]/)
    .map((s) => s.trim())
    .filter(Boolean)
}

function whyNext(goal: GoalRow): string {
  const latestCycle = goal.pursuit?.history?.[goal.pursuit.history.length - 1]
  if (latestCycle?.notes) return String(latestCycle.notes)
  if (latestCycle?.decided_kind) return `decided:${latestCycle.decided_kind}`
  const latest = goal.decisionHistory[goal.decisionHistory.length - 1]
  if (latest?.reason) return String(latest.reason)
  if (latest?.action) return String(latest.action)
  if (goal.strategy) return goal.strategy
  return 'no_decision_recorded'
}

export function GoalsPanel({
  snap,
  loadOpts,
  onSelectGoal,
  onGoalsChanged,
  onPursuitStarted,
}: Props) {
  const selected =
    snap.goals.find((g) => g.id === snap.selectedGoalId) ?? snap.goals[0] ?? null

  const [projectId, setProjectId] = useState(
    snap.projects[0]?.projectId ?? selected?.projectId ?? 'proj_demo',
  )
  const [desiredOutcome, setDesiredOutcome] = useState('')
  const [criteria, setCriteria] = useState('operator review')
  const [agents, setAgents] = useState('planner, extractor, verifier')
  const [capabilities, setCapabilities] = useState('code.read, tests.run')
  const [maxCalls, setMaxCalls] = useState('50')
  const [maxWall, setMaxWall] = useState('3600')
  const [strategy, setStrategy] = useState('')
  const [redirectReason, setRedirectReason] = useState('')
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionNote, setActionNote] = useState<string | null>(null)

  const live = snap.mode === 'live' && !!loadOpts.baseUrl

  const replaceGoal = (goal: GoalRow) => {
    const others = snap.goals.filter((g) => g.id !== goal.id)
    onGoalsChanged([goal, ...others], goal.id)
  }

  const runLive = async (label: string, fn: () => Promise<void>) => {
    if (!live || !loadOpts.baseUrl) {
      setActionError('Live goal actions require ?mode=live&baseUrl=…')
      return
    }
    setBusy(label)
    setActionError(null)
    setActionNote(null)
    try {
      await fn()
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'action_failed')
    } finally {
      setBusy(null)
    }
  }

  const handleCreate = () =>
    runLive('create', async () => {
      const goal = await createLiveGoal({
        baseUrl: loadOpts.baseUrl!,
        token: loadOpts.token,
        projectId,
        desiredOutcome: desiredOutcome.trim() || 'Untitled goal',
        verificationCriteria: parseCsv(criteria),
        permittedAgents: parseCsv(agents),
        strategy: strategy.trim(),
        resourceEnvelope: {
          max_model_calls: Number(maxCalls) || 50,
          max_wall_time_seconds: Number(maxWall) || 3600,
          max_graph_nodes: 50,
          max_active_sessions: 4,
        },
        authorityEnvelope: {
          allowed_capabilities: parseCsv(capabilities),
          intervention: 'operator_may_pause_redirect_resume',
        },
        stopConditions: ['operator_cancel', 'budget_exhausted'],
      })
      replaceGoal(goal)
      setActionNote(`Created ${goal.id}`)
      setDesiredOutcome('')
    })

  const handleStart = () => {
    if (!selected) return
    if (!live) {
      const cycleNote = 'Mock: pursuit tick (fixture) — decided:act'
      const now = new Date().toISOString()
      const updated: GoalRow = {
        ...selected,
        pursuit: {
          goal_id: selected.id,
          schedule: selected.pursuit?.schedule ?? {},
          history: [
            ...(selected.pursuit?.history ?? []),
            {
              cycle_id: `cyc_mock_${Date.now()}`,
              phase: 'update',
              decided_kind: 'act',
              notes: cycleNote,
              at: now,
            },
          ],
          commitments: selected.pursuit?.commitments ?? [],
          adopted_lessons: selected.pursuit?.adopted_lessons ?? [],
        },
        updatedAt: now,
      }
      replaceGoal(updated)
      setActionNote(cycleNote)
      return
    }
    void runLive('pursue', async () => {
      const { goal, cycle } = await startLivePursuit({
        baseUrl: loadOpts.baseUrl!,
        token: loadOpts.token,
        goal: selected,
      })
      replaceGoal(goal)
      const missionId =
        (typeof cycle?.proposal === 'object' &&
          cycle.proposal &&
          (cycle.proposal as { mission_id?: string }).mission_id) ||
        goal.missionIds[goal.missionIds.length - 1]
      onPursuitStarted(goal, missionId)
      const kind = cycle?.decided_kind ? String(cycle.decided_kind) : 'tick'
      setActionNote(`Pursuit tick · ${kind}${missionId ? ` · mission ${missionId}` : ''}`)
    })
  }

  const handleTransition = (status: GoalStatus, reason: string) => {
    if (!selected) return
    if (!live) {
      const history = [
        ...selected.decisionHistory,
        {
          at: new Date().toISOString(),
          actor: 'fixture',
          from: selected.status,
          to: status,
          reason,
        },
      ]
      replaceGoal({ ...selected, status, decisionHistory: history, updatedAt: new Date().toISOString() })
      setActionNote(`Mock transition → ${status}`)
      return
    }
    void runLive(status, async () => {
      const goal = await transitionLiveGoal({
        baseUrl: loadOpts.baseUrl!,
        token: loadOpts.token,
        goalId: selected.id,
        status,
        reason,
      })
      replaceGoal(goal)
      setActionNote(`Goal ${status}`)
    })
  }

  const handleRedirect = () => {
    const reason = redirectReason.trim() || 'operator redirect'
    if (!selected) return
    if (!live) {
      const now = new Date().toISOString()
      replaceGoal({
        ...selected,
        status: 'active',
        updatedAt: now,
        decisionHistory: [
          ...selected.decisionHistory,
          {
            at: now,
            actor: 'fixture',
            from: selected.status,
            to: 'paused',
            reason: `redirect:${reason}`,
          },
          {
            at: now,
            actor: 'fixture',
            from: 'paused',
            to: 'active',
            reason: `redirect_resume:${reason}`,
          },
        ],
      })
      setActionNote(`Mock redirect recorded: ${reason}`)
      return
    }
    void runLive('redirect', async () => {
      let goal = selected
      if (goal.status === 'active') {
        goal = await transitionLiveGoal({
          baseUrl: loadOpts.baseUrl!,
          token: loadOpts.token,
          goalId: goal.id,
          status: 'paused',
          reason: `redirect:${reason}`,
        })
      }
      if (goal.status === 'paused') {
        goal = await transitionLiveGoal({
          baseUrl: loadOpts.baseUrl!,
          token: loadOpts.token,
          goalId: goal.id,
          status: 'active',
          reason: `redirect_resume:${reason}`,
        })
      }
      const { goal: ticked, cycle } = await startLivePursuit({
        baseUrl: loadOpts.baseUrl!,
        token: loadOpts.token,
        goal,
      })
      replaceGoal(ticked)
      const missionId =
        (typeof cycle?.proposal === 'object' &&
          cycle.proposal &&
          (cycle.proposal as { mission_id?: string }).mission_id) ||
        ticked.missionIds[ticked.missionIds.length - 1]
      onPursuitStarted(ticked, missionId)
      setRedirectReason('')
      setActionNote(`Redirected · pursuit tick${missionId ? ` · ${missionId}` : ''}`)
    })
  }

  return (
    <Panel
      title="Goal pursuit"
      subtitle="Create → agents/resources → pursue → progress/blockers → interrupt/redirect/resume → why-next"
      testId="goals-panel"
    >
      <div className="actions" data-testid="goal-picker">
        <label htmlFor="goal-select">
          Focus goal{' '}
          <select
            id="goal-select"
            data-testid="goal-select"
            value={selected?.id ?? ''}
            onChange={(e) => onSelectGoal(e.target.value)}
          >
            {snap.goals.length === 0 ? <option value="">(none)</option> : null}
            {snap.goals.map((g) => (
              <option key={g.id} value={g.id}>
                {g.id.slice(0, 14)}… · {g.status} · {g.desiredOutcome.slice(0, 48)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <section className="goal-create" data-testid="goal-create">
        <h3>Create goal</h3>
        <p className="muted">Same fields as POST /v1/goals — agents, resources, permissions.</p>
        <div className="form-grid">
          <label>
            Project
            <input
              data-testid="goal-project"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            />
          </label>
          <label>
            Desired outcome
            <input
              data-testid="goal-outcome"
              value={desiredOutcome}
              onChange={(e) => setDesiredOutcome(e.target.value)}
              placeholder="What should be true when achieved?"
            />
          </label>
          <label>
            Verification criteria
            <input
              data-testid="goal-criteria"
              value={criteria}
              onChange={(e) => setCriteria(e.target.value)}
            />
          </label>
          <label>
            Permitted agents
            <input
              data-testid="goal-agents"
              value={agents}
              onChange={(e) => setAgents(e.target.value)}
            />
          </label>
          <label>
            Allowed capabilities
            <input
              data-testid="goal-capabilities"
              value={capabilities}
              onChange={(e) => setCapabilities(e.target.value)}
            />
          </label>
          <label>
            Max model calls
            <input
              data-testid="goal-max-calls"
              value={maxCalls}
              onChange={(e) => setMaxCalls(e.target.value)}
            />
          </label>
          <label>
            Max wall time (s)
            <input
              data-testid="goal-max-wall"
              value={maxWall}
              onChange={(e) => setMaxWall(e.target.value)}
            />
          </label>
          <label>
            Strategy
            <input
              data-testid="goal-strategy"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            />
          </label>
        </div>
        <div className="actions">
          <button
            type="button"
            data-testid="goal-create-btn"
            disabled={!!busy}
            onClick={() => void handleCreate()}
          >
            {busy === 'create' ? 'Creating…' : 'Create goal'}
          </button>
        </div>
      </section>

      {selected ? (
        <section className="goal-detail" data-testid="goal-detail">
          <h3>
            <code>{selected.id}</code> <StatusBadge kind="generic" value={selected.status} />
          </h3>
          <p className="objective">{selected.desiredOutcome}</p>
          <dl className="metrics">
            <div>
              <dt>Owner</dt>
              <dd>{selected.owner}</dd>
            </div>
            <div>
              <dt>Agents</dt>
              <dd>{selected.permittedAgents.join(', ') || '—'}</dd>
            </div>
            <div>
              <dt>Capabilities</dt>
              <dd>
                {Array.isArray(selected.authorityEnvelope.allowed_capabilities)
                  ? (selected.authorityEnvelope.allowed_capabilities as string[]).join(', ')
                  : '—'}
              </dd>
            </div>
            <div>
              <dt>Linked missions</dt>
              <dd>{selected.missionIds.join(', ') || '—'}</dd>
            </div>
          </dl>

          <h4>Progress & blockers</h4>
          <ul data-testid="goal-blockers">
            {selected.blockers.length === 0 ? <li className="muted">No blockers recorded.</li> : null}
            {selected.blockers.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <ul data-testid="goal-questions">
            {selected.openQuestions.map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>

          <h4>Why next</h4>
          <p data-testid="goal-why-next">{whyNext(selected)}</p>
          <p className="muted">Strategy: {selected.strategy || '—'}</p>
          {selected.pursuit?.history?.length ? (
            <table className="grid" data-testid="pursuit-cycle-history">
              <thead>
                <tr>
                  <th>Cycle</th>
                  <th>Phase</th>
                  <th>Kind</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {selected.pursuit.history.map((c, i) => (
                  <tr key={String(c.cycle_id ?? i)}>
                    <td>
                      <code>{String(c.cycle_id ?? i)}</code>
                    </td>
                    <td>{String(c.phase ?? '—')}</td>
                    <td>{String(c.decided_kind ?? '—')}</td>
                    <td>{String(c.notes ?? '—')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          <h4>Decision history</h4>
          <table className="grid" data-testid="goal-decision-history">
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Transition</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {selected.decisionHistory.map((d, i) => (
                <tr key={`${d.at}-${i}`}>
                  <td>{d.at}</td>
                  <td>{d.actor}</td>
                  <td>
                    {d.action ? `${d.action} ` : ''}
                    {d.from ?? '?'} → {d.to ?? '?'}
                  </td>
                  <td>{d.reason ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {selected.decisionHistory.length === 0 ? (
            <p className="muted">No decisions yet.</p>
          ) : null}

          <div className="actions" data-testid="goal-actions">
            <button
              type="button"
              data-testid="goal-start-pursuit"
              disabled={!!busy}
              onClick={handleStart}
            >
              {busy === 'pursue' ? 'Starting…' : 'Start pursuit'}
            </button>
            <button
              type="button"
              data-testid="goal-interrupt"
              disabled={!!busy}
              onClick={() => handleTransition('paused', 'operator interrupt')}
            >
              Interrupt
            </button>
            <button
              type="button"
              data-testid="goal-resume"
              disabled={!!busy}
              onClick={() => handleTransition('active', 'operator resume')}
            >
              Resume
            </button>
            <button
              type="button"
              data-testid="goal-cancel"
              disabled={!!busy}
              onClick={() => handleTransition('cancelled', 'operator cancel')}
            >
              Cancel
            </button>
          </div>

          <div className="actions" data-testid="goal-redirect">
            <input
              data-testid="goal-redirect-reason"
              value={redirectReason}
              onChange={(e) => setRedirectReason(e.target.value)}
              placeholder="Redirect reason / new direction"
            />
            <button
              type="button"
              data-testid="goal-redirect-btn"
              disabled={!!busy}
              onClick={handleRedirect}
            >
              {busy === 'redirect' ? 'Redirecting…' : 'Redirect'}
            </button>
          </div>
        </section>
      ) : (
        <p data-testid="empty-goals">No goals yet — create one above.</p>
      )}

      {actionError ? (
        <p className="banner-error" role="alert" data-testid="goal-action-error">
          {actionError}
        </p>
      ) : null}
      {actionNote ? (
        <p className="muted" data-testid="goal-action-note">
          {actionNote}
        </p>
      ) : null}
      {!live && snap.mode === 'live' ? (
        <p className="muted" data-testid="goal-live-hint">
          Add <code>?baseUrl=</code> to mutate goals against the API.
        </p>
      ) : null}
    </Panel>
  )
}
