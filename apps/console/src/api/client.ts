/** Browser API client — never embeds provider secrets. */

import type {
  ConsoleSnapshot,
  GoalDecision,
  GoalKind,
  GoalMissionOutcome,
  GoalProgressEntry,
  GoalRow,
  GoalStatus,
  HistoryRow,
  MissionGraph,
  MissionTask,
  OpsEventRow,
  OpsView,
  PursuitStatus,
  SchedulerQueueRow,
} from './types'
import { MOCK_OPS, MOCK_SNAPSHOT } from '../data/fixtures'

const SECRET_RE = /(sk-[a-zA-Z0-9]+|api_key\s*=\s*\S+)/i
export const PUBLIC_HOSTNAME = 'swarm.splitsignal.ai'

export function scrubSecrets(value: string): string {
  return value.replace(SECRET_RE, '[redacted]')
}

export function assertNoSecretsInBundle(payload: unknown): void {
  const blob = JSON.stringify(payload)
  if (SECRET_RE.test(blob)) {
    throw new Error('secret_material_detected_in_console_payload')
  }
}

function emptyLiveMission(): MissionGraph {
  return {
    missionId: '(none)',
    revision: 0,
    status: 'empty',
    objective: 'No durable missions yet — submit via API/CLI or create from console live mode.',
    tasks: [],
    planningRoles: [],
    logicalAgents: 0,
    busyWorkers: 0,
    inFlightInference: 0,
  }
}

/** Honest empty operational snapshot — no fixture routes/workers/profiles. */
export function emptyLiveSnapshot(opts?: {
  mission?: MissionGraph
  history?: HistoryRow[]
  capacity?: ConsoleSnapshot['capacity']
  routes?: ConsoleSnapshot['routes']
  workers?: ConsoleSnapshot['workers']
  projects?: ConsoleSnapshot['projects']
  artifacts?: ConsoleSnapshot['artifacts']
  events?: ConsoleSnapshot['events']
  approvals?: ConsoleSnapshot['approvals']
  goals?: GoalRow[]
  selectedGoalId?: string | null
  errors?: string[]
  mockVsLive?: string
  serverReady?: boolean | null
}): ConsoleSnapshot {
  return {
    mode: 'live',
    mockVsLive:
      opts?.mockVsLive ??
      'operational_empty_or_observed_from_api_not_fixture_catalog',
    hostnamePublic: PUBLIC_HOSTNAME,
    serverReady: opts?.serverReady ?? null,
    mission: opts?.mission ?? emptyLiveMission(),
    goals: opts?.goals ?? [],
    selectedGoalId: opts?.selectedGoalId ?? null,
    routes: opts?.routes ?? [],
    capacity: opts?.capacity ?? [],
    capacityUnknown: !(opts?.capacity && opts.capacity.length),
    workers: opts?.workers ?? [],
    profiles: [],
    approvals: opts?.approvals ?? [],
    projects: opts?.projects ?? [],
    history: opts?.history ?? [],
    artifacts: opts?.artifacts ?? [],
    events: opts?.events ?? [],
    streamInterrupted: false,
    errors: opts?.errors ?? [],
  }
}

export function goalFromApi(raw: Record<string, unknown>): GoalRow {
  const historyRaw = Array.isArray(raw.decision_history) ? raw.decision_history : []
  const decisionHistory: GoalDecision[] = historyRaw
    .filter((row): row is Record<string, unknown> => !!row && typeof row === 'object')
    .map((row) => ({
      at: String(row.at ?? ''),
      actor: String(row.actor ?? ''),
      from: row.from != null ? String(row.from) : undefined,
      to: row.to != null ? String(row.to) : undefined,
      action: row.action != null ? String(row.action) : undefined,
      reason: row.reason != null ? String(row.reason) : undefined,
      ...row,
    }))
  const progressRaw = Array.isArray(raw.progress) ? raw.progress : []
  const progress: GoalProgressEntry[] = progressRaw
    .filter((row): row is Record<string, unknown> => !!row && typeof row === 'object')
    .map((row) => ({
      at: String(row.at ?? ''),
      actor: String(row.actor ?? ''),
      summary: String(row.summary ?? ''),
      metrics: (row.metrics as Record<string, unknown>) ?? {},
    }))
  const outcomesRaw = Array.isArray(raw.mission_outcomes) ? raw.mission_outcomes : []
  const missionOutcomes: GoalMissionOutcome[] = outcomesRaw
    .filter((row): row is Record<string, unknown> => !!row && typeof row === 'object')
    .map((row) => ({
      at: String(row.at ?? ''),
      mission_id: String(row.mission_id ?? ''),
      outcome: String(row.outcome ?? ''),
      actor: String(row.actor ?? ''),
      notes: row.notes != null ? String(row.notes) : undefined,
      evidence_refs: Array.isArray(row.evidence_refs) ? (row.evidence_refs as string[]) : [],
    }))
  return {
    id: String(raw.id ?? ''),
    projectId: String(raw.project_id ?? ''),
    desiredOutcome: String(raw.desired_outcome ?? ''),
    verificationCriteria: Array.isArray(raw.verification_criteria)
      ? (raw.verification_criteria as string[])
      : [],
    kind: (String(raw.kind ?? 'finite') as GoalKind) || 'finite',
    scope: (raw.scope as Record<string, unknown>) ?? {},
    constraints: (raw.constraints as Record<string, unknown>) ?? {},
    resourceEnvelope: (raw.resource_envelope as Record<string, unknown>) ?? {},
    authorityEnvelope: (raw.authority_envelope as Record<string, unknown>) ?? {},
    owner: String(raw.owner ?? 'operator'),
    permittedAgents: Array.isArray(raw.permitted_agents)
      ? (raw.permitted_agents as string[])
      : [],
    strategy: String(raw.strategy ?? ''),
    evidenceRefs: Array.isArray(raw.evidence_refs) ? (raw.evidence_refs as string[]) : [],
    missionIds: Array.isArray(raw.mission_ids) ? (raw.mission_ids as string[]) : [],
    dependencies: Array.isArray(raw.dependencies) ? (raw.dependencies as string[]) : [],
    missionOutcomes,
    openQuestions: Array.isArray(raw.open_questions) ? (raw.open_questions as string[]) : [],
    blockers: Array.isArray(raw.blockers) ? (raw.blockers as string[]) : [],
    stopConditions: Array.isArray(raw.stop_conditions) ? (raw.stop_conditions as string[]) : [],
    reviewCadence: (raw.review_cadence as string | null) ?? null,
    expiresAt: (raw.expires_at as string | null) ?? null,
    status: String(raw.status ?? 'active') as GoalStatus,
    progress,
    decisionHistory,
    triggerReceipts: Array.isArray(raw.trigger_receipts)
      ? (raw.trigger_receipts as Array<Record<string, unknown>>)
      : [],
    restartCount: Number(raw.restart_count ?? 0),
    createdAt: String(raw.created_at ?? ''),
    updatedAt: String(raw.updated_at ?? ''),
    pursuit: null,
  }
}

async function mutateJson(
  url: string,
  headers: Record<string, string>,
  method: 'POST' | 'PUT' | 'PATCH',
  body: unknown,
): Promise<Record<string, unknown>> {
  const res = await fetch(url, {
    method,
    headers: { ...headers, 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`api_error_${res.status}`)
  }
  const payload = await res.json()
  assertNoSecretsInBundle(payload)
  return payload as Record<string, unknown>
}

export type GoalCreateInput = {
  baseUrl: string
  token?: string
  projectId: string
  desiredOutcome: string
  verificationCriteria?: string[]
  kind?: GoalKind | string
  permittedAgents?: string[]
  resourceEnvelope?: Record<string, unknown>
  authorityEnvelope?: Record<string, unknown>
  strategy?: string
  stopConditions?: string[]
}

export async function createLiveGoal(opts: GoalCreateInput): Promise<GoalRow> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const payload = await mutateJson(`${opts.baseUrl.replace(/\/$/, '')}/v1/goals`, headers, 'POST', {
    project_id: opts.projectId,
    desired_outcome: opts.desiredOutcome,
    verification_criteria: opts.verificationCriteria ?? [],
    kind: opts.kind ?? 'finite',
    permitted_agents: opts.permittedAgents ?? [],
    resource_envelope: opts.resourceEnvelope ?? {},
    authority_envelope: opts.authorityEnvelope ?? {},
    strategy: opts.strategy ?? '',
    stop_conditions: opts.stopConditions ?? [],
  })
  return goalFromApi((payload.goal ?? {}) as Record<string, unknown>)
}

async function lifecycleLiveGoal(opts: {
  baseUrl: string
  token?: string
  goalId: string
  action: 'pause' | 'resume' | 'cancel' | 'restart'
  reason?: string
}): Promise<GoalRow> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const payload = await mutateJson(
    `${base}/v1/goals/${encodeURIComponent(opts.goalId)}/${opts.action}`,
    headers,
    'POST',
    { reason: opts.reason ?? 'operator' },
  )
  return goalFromApi((payload.goal ?? {}) as Record<string, unknown>)
}

export async function transitionLiveGoal(opts: {
  baseUrl: string
  token?: string
  goalId: string
  status: GoalStatus | string
  reason?: string
}): Promise<GoalRow> {
  // Prefer Lane C named lifecycle endpoints when status maps cleanly.
  const map: Record<string, 'pause' | 'resume' | 'cancel' | 'restart'> = {
    paused: 'pause',
    active: 'resume',
    cancelled: 'cancel',
  }
  const action = map[String(opts.status)]
  if (action) {
    try {
      return await lifecycleLiveGoal({
        baseUrl: opts.baseUrl,
        token: opts.token,
        goalId: opts.goalId,
        action,
        reason: opts.reason,
      })
    } catch {
      // Fall through to generic transition (e.g. resume from waiting/blocked).
    }
  }
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const payload = await mutateJson(
    `${base}/v1/goals/${encodeURIComponent(opts.goalId)}/transition`,
    headers,
    'POST',
    { status: opts.status, reason: opts.reason ?? 'operator' },
  )
  return goalFromApi((payload.goal ?? {}) as Record<string, unknown>)
}

export async function linkLiveGoalMission(opts: {
  baseUrl: string
  token?: string
  goalId: string
  missionId: string
}): Promise<GoalRow> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const payload = await mutateJson(
    `${base}/v1/goals/${encodeURIComponent(opts.goalId)}/missions`,
    headers,
    'POST',
    { mission_id: opts.missionId },
  )
  return goalFromApi((payload.goal ?? {}) as Record<string, unknown>)
}

/** Lane D: POST /v1/goals/{id}/pursuit/tick */
export async function tickLivePursuit(opts: {
  baseUrl: string
  token?: string
  goalId: string
  force?: boolean
}): Promise<{ goal: GoalRow; cycle: Record<string, unknown> | null }> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const payload = await mutateJson(
    `${base}/v1/goals/${encodeURIComponent(opts.goalId)}/pursuit/tick`,
    headers,
    'POST',
    { force: opts.force ?? true },
  )
  return {
    goal: goalFromApi((payload.goal ?? {}) as Record<string, unknown>),
    cycle: (payload.cycle as Record<string, unknown>) ?? null,
  }
}

/** Lane D: GET /v1/goals/{id}/pursuit */
export async function fetchLivePursuitStatus(opts: {
  baseUrl: string
  token?: string
  goalId: string
}): Promise<PursuitStatus> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const res = await fetchJson(
    `${base}/v1/goals/${encodeURIComponent(opts.goalId)}/pursuit`,
    headers,
  )
  if (!res.ok) {
    throw new Error(`api_error_${res.status}`)
  }
  const body = (res.body ?? {}) as Record<string, unknown>
  return {
    goal_id: String(body.goal_id ?? opts.goalId),
    schedule: (body.schedule as Record<string, unknown>) ?? {},
    history: Array.isArray(body.history) ? (body.history as PursuitStatus['history']) : [],
    commitments: Array.isArray(body.commitments) ? (body.commitments as string[]) : [],
    adopted_lessons: Array.isArray(body.adopted_lessons)
      ? (body.adopted_lessons as Array<Record<string, unknown>>)
      : [],
  }
}

/** Start pursuit = Lane C resume if needed + Lane D tick (same as SDK). */
export async function startLivePursuit(opts: {
  baseUrl: string
  token?: string
  goal: GoalRow
}): Promise<{ goal: GoalRow; cycle: Record<string, unknown> | null; pursuit: PursuitStatus | null }> {
  let goal = opts.goal
  if (goal.status === 'paused') {
    goal = await lifecycleLiveGoal({
      baseUrl: opts.baseUrl,
      token: opts.token,
      goalId: goal.id,
      action: 'resume',
      reason: 'start_pursuit',
    })
  } else if (goal.status === 'cancelled' || goal.status === 'expired') {
    goal = await lifecycleLiveGoal({
      baseUrl: opts.baseUrl,
      token: opts.token,
      goalId: goal.id,
      action: 'restart',
      reason: 'start_pursuit',
    })
  }
  const ticked = await tickLivePursuit({
    baseUrl: opts.baseUrl,
    token: opts.token,
    goalId: goal.id,
    force: true,
  })
  let pursuit: PursuitStatus | null = null
  try {
    pursuit = await fetchLivePursuitStatus({
      baseUrl: opts.baseUrl,
      token: opts.token,
      goalId: goal.id,
    })
  } catch {
    pursuit = null
  }
  return { goal: { ...ticked.goal, pursuit }, cycle: ticked.cycle, pursuit }
}

function missionFromApi(raw: Record<string, unknown>, tasks: MissionTask[] = []): MissionGraph {
  return {
    missionId: String(raw.id ?? raw.mission_id ?? '(unknown)'),
    revision: Number(raw.revision ?? 1),
    status: String(raw.status ?? 'unknown'),
    objective: String(raw.objective ?? raw.goal ?? ''),
    tasks,
    planningRoles: [],
    logicalAgents: 0,
    busyWorkers: 0,
    inFlightInference: 0,
  }
}

function tasksFromGraph(graph: Record<string, unknown>): MissionTask[] {
  const rows = Array.isArray(graph.tasks) ? (graph.tasks as Array<Record<string, unknown>>) : []
  return rows.map((t) => ({
    id: String(t.id ?? t.task_id ?? ''),
    objective: String(t.objective ?? t.goal ?? ''),
    status: String(t.status ?? 'unknown'),
    roleHint: (t.role_hint as string | undefined) ?? (t.roleHint as string | undefined),
    waitingReason:
      (t.waiting_reason as string | undefined) ?? (t.waitingReason as string | undefined),
    unblockEvent:
      (t.unblock_event as string | undefined) ?? (t.unblockEvent as string | undefined),
  }))
}

function historyFromList(items: Array<Record<string, unknown>>): HistoryRow[] {
  return items.map((row) => ({
    missionId: String(row.mission_id ?? ''),
    projectId: (row.project_id as string | null) ?? null,
    goal: String(row.objective ?? row.goal ?? ''),
    status: String(row.status ?? 'unknown'),
    costUsd: Number(row.cost_usd ?? 0),
    artifactCount: Number(row.artifact_count ?? 0),
    tags: [String(row.source ?? 'mission_store')],
    updatedAt: String(row.updated_at ?? ''),
  }))
}

async function fetchJson(
  url: string,
  headers: Record<string, string>,
): Promise<{ ok: boolean; status: number; body: unknown }> {
  const res = await fetch(url, { headers })
  if (!res.ok) {
    return { ok: false, status: res.status, body: null }
  }
  const body = await res.json()
  assertNoSecretsInBundle(body)
  return { ok: true, status: res.status, body }
}

export async function createLiveMission(opts: {
  baseUrl: string
  token?: string
  objective: string
  projectId: string
}): Promise<MissionGraph> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const body = {
    mission: {
      project_id: opts.projectId,
      objective: opts.objective,
      acceptance_criteria: ['operator review'],
      allowed_capabilities: ['code.read'],
      data_scope_ids: ['scope_local'],
      resource_policy_id: 'policy_default',
      max_wall_time_seconds: 3600,
      max_graph_nodes: 50,
      max_active_sessions: 4,
      max_model_calls: 50,
    },
  }
  const res = await fetch(`${opts.baseUrl}/v1/missions`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`api_error_${res.status}`)
  }
  const payload = await res.json()
  assertNoSecretsInBundle(payload)
  return missionFromApi((payload.mission ?? {}) as Record<string, unknown>)
}

export async function loadSnapshot(opts: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
  missionId?: string
  goalId?: string
}): Promise<ConsoleSnapshot> {
  // Fixture UI is explicit mock mode only — never mixed into live/operational.
  if (opts.mode === 'mock') {
    const snap = structuredClone(MOCK_SNAPSHOT)
    if (opts.goalId) {
      snap.selectedGoalId = opts.goalId
    }
    assertNoSecretsInBundle(snap)
    return snap
  }

  if (!opts.baseUrl) {
    const snap = emptyLiveSnapshot({
      errors: [
        'Live mode with no baseUrl — showing empty operational state (not mock fixtures).',
      ],
      mockVsLive: 'operational_empty_no_api_base_not_fixture_catalog',
      serverReady: null,
    })
    assertNoSecretsInBundle(snap)
    return snap
  }

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')

  const [
    readyRes,
    capacityRes,
    missionsRes,
    routesRes,
    workersRes,
    projectsRes,
    goalsRes,
    approvalsRes,
  ] = await Promise.all([
    fetchJson(`${base}/health/ready`, headers),
    fetchJson(`${base}/v1/capacity`, headers),
    fetchJson(`${base}/v1/missions`, headers),
    fetchJson(`${base}/v1/routes`, headers),
    fetchJson(`${base}/v1/workers`, headers),
    fetchJson(`${base}/v1/projects`, headers),
    fetchJson(`${base}/v1/goals`, headers),
    fetchJson(`${base}/v1/approvals`, headers),
  ])

  if (!capacityRes.ok) {
    throw new Error(`api_error_${capacityRes.status}`)
  }
  if (!missionsRes.ok) {
    throw new Error(`api_error_${missionsRes.status}`)
  }

  const capacity = capacityRes.body as Record<string, unknown>
  const missionsPayload = missionsRes.body as Record<string, unknown>
  const serverReady =
    readyRes.ok &&
    typeof readyRes.body === 'object' &&
    readyRes.body !== null &&
    (readyRes.body as { status?: string }).status === 'ready'

  const goals: GoalRow[] = []
  if (goalsRes.ok) {
    const goalsPayload = goalsRes.body as Record<string, unknown>
    for (const row of (goalsPayload.goals ?? []) as Array<Record<string, unknown>>) {
      goals.push(goalFromApi(row))
    }
  }

  const preferredGoalId = (opts.goalId || '').trim()
  const selectedGoalId =
    (preferredGoalId && goals.some((g) => g.id === preferredGoalId) && preferredGoalId) ||
    goals[0]?.id ||
    null

  if (selectedGoalId) {
    const pursuitRes = await fetchJson(
      `${base}/v1/goals/${encodeURIComponent(selectedGoalId)}/pursuit`,
      headers,
    )
    if (pursuitRes.ok) {
      const body = (pursuitRes.body ?? {}) as Record<string, unknown>
      const idx = goals.findIndex((g) => g.id === selectedGoalId)
      if (idx >= 0) {
        goals[idx] = {
          ...goals[idx],
          pursuit: {
            goal_id: String(body.goal_id ?? selectedGoalId),
            schedule: (body.schedule as Record<string, unknown>) ?? {},
            history: Array.isArray(body.history)
              ? (body.history as NonNullable<GoalRow['pursuit']>['history'])
              : [],
            commitments: Array.isArray(body.commitments) ? (body.commitments as string[]) : [],
            adopted_lessons: Array.isArray(body.adopted_lessons)
              ? (body.adopted_lessons as Array<Record<string, unknown>>)
              : [],
          },
        }
      }
    }
  }

  const items = Array.isArray(missionsPayload.missions)
    ? (missionsPayload.missions as Array<Record<string, unknown>>)
    : Array.isArray(missionsPayload.items)
      ? (missionsPayload.items as Array<Record<string, unknown>>)
      : []

  const preferredId = (opts.missionId || '').trim()
  const selectedGoal = goals.find((g) => g.id === selectedGoalId) ?? null
  const linkedPreferred =
    selectedGoal &&
    selectedGoal.missionIds.length > 0 &&
    items.find((row) => selectedGoal.missionIds.includes(String(row.mission_id ?? row.id ?? '')))
  const selectedRow =
    (preferredId && items.find((row) => String(row.mission_id ?? '') === preferredId)) ||
    linkedPreferred ||
    items[0] ||
    null

  let mission = emptyLiveMission()
  let artifacts: ConsoleSnapshot['artifacts'] = []
  let events: ConsoleSnapshot['events'] = []

  if (selectedRow) {
    const missionId = String(selectedRow.mission_id ?? selectedRow.id ?? '')
    const [detailRes, graphRes, artsRes, eventsRes] = await Promise.all([
      fetchJson(`${base}/v1/missions/${missionId}`, headers),
      fetchJson(`${base}/v1/missions/${missionId}/graph`, headers),
      fetchJson(`${base}/v1/missions/${missionId}/artifacts`, headers),
      fetchJson(`${base}/v1/events?mission_id=${encodeURIComponent(missionId)}&limit=50`, headers),
    ])

    const tasks = graphRes.ok
      ? tasksFromGraph((graphRes.body ?? {}) as Record<string, unknown>)
      : []

    if (detailRes.ok) {
      const detail = detailRes.body as Record<string, unknown>
      mission = missionFromApi((detail.mission ?? selectedRow) as Record<string, unknown>, tasks)
    } else {
      mission = missionFromApi(selectedRow, tasks)
    }

    if (artsRes.ok) {
      const artsBody = artsRes.body as Record<string, unknown>
      const rows = Array.isArray(artsBody.artifacts)
        ? (artsBody.artifacts as Array<Record<string, unknown>>)
        : []
      artifacts = rows.map((a) => ({
        artifactId: String(a.artifact_id ?? a.id ?? ''),
        kind: String(a.kind ?? 'artifact'),
        uri: (a.uri as string | undefined) ?? undefined,
        summary: (a.summary as string | undefined) ?? undefined,
        contentHash:
          (a.content_hash as string | undefined) ?? (a.sha256 as string | undefined) ?? undefined,
        mediaType: (a.media_type as string | undefined) ?? undefined,
        byteLength:
          typeof a.byte_length === 'number'
            ? a.byte_length
            : typeof a.byteLength === 'number'
              ? a.byteLength
              : undefined,
      }))
    }

    if (eventsRes.ok) {
      const evBody = eventsRes.body as Record<string, unknown>
      const rows = Array.isArray(evBody.items)
        ? (evBody.items as Array<Record<string, unknown>>)
        : Array.isArray(evBody.events)
          ? (evBody.events as Array<Record<string, unknown>>)
          : []
      events = rows.map((e, idx) => ({
        id: String(e.id ?? e.event_id ?? `evt_${idx}`),
        type: String(e.type ?? e.event_type ?? 'event'),
        summary: String(e.summary ?? e.type ?? e.event_type ?? ''),
      }))
    }
  }

  const routes: ConsoleSnapshot['routes'] = []
  if (routesRes.ok) {
    const routesPayload = routesRes.body as Record<string, unknown>
    for (const row of (routesPayload.routes ?? []) as Array<Record<string, unknown>>) {
      routes.push({
        routeId: String(row.route_id ?? row.routeId ?? ''),
        provider: String(row.provider ?? row.provider_id ?? 'unknown'),
        modelId: (row.model_id as string | null) ?? null,
        availability: String(
          row.availability_status ?? row.availability ?? 'unknown',
        ) as ConsoleSnapshot['routes'][0]['availability'],
        status: String(row.status ?? 'unknown'),
        capabilityClaims: Array.isArray(row.observed_capabilities)
          ? (row.observed_capabilities as string[])
          : Array.isArray(row.capabilityClaims)
            ? (row.capabilityClaims as string[])
            : [],
      })
    }
  }

  const workers: ConsoleSnapshot['workers'] = []
  if (workersRes.ok) {
    const workersPayload = workersRes.body as Record<string, unknown>
    for (const row of (workersPayload.workers ?? []) as Array<Record<string, unknown>>) {
      const leasesRaw = row.active_leases ?? row.activeLeases
      workers.push({
        workerId: String(row.worker_id ?? row.workerId ?? ''),
        status: String(row.status ?? 'unknown'),
        generation: Number(row.generation ?? 0),
        capacity: Number(row.capacity ?? 0),
        privacy: Array.isArray(row.privacy) ? (row.privacy as string[]) : [],
        claimed: (row.claimed as string | null) ?? null,
        activeLeases: Array.isArray(leasesRaw) ? leasesRaw.map((x) => String(x)) : [],
        revoked: Boolean(row.revoked),
        stale: Boolean(row.stale),
      })
    }
  }

  const projects: ConsoleSnapshot['projects'] = []
  if (projectsRes.ok) {
    const projectsPayload = projectsRes.body as Record<string, unknown>
    for (const row of (projectsPayload.projects ?? []) as Array<Record<string, unknown>>) {
      projects.push({
        projectId: String(row.project_id ?? ''),
        name: String(row.name ?? ''),
        repoPath: String(row.repo_path ?? ''),
        allowPaid: Boolean(row.allow_paid),
        allowedTools: Array.isArray(row.allowed_tools) ? (row.allowed_tools as string[]) : [],
        updatedAt: String(row.updated_at ?? ''),
      })
    }
  }

  const approvals: ConsoleSnapshot['approvals'] = []
  if (approvalsRes.ok) {
    const approvalsPayload = approvalsRes.body as Record<string, unknown>
    for (const row of (approvalsPayload.approvals ?? []) as Array<Record<string, unknown>>) {
      approvals.push({
        id: String(row.id ?? row.approval_id ?? ''),
        operation: String(row.operation ?? row.op ?? 'unknown'),
        destination: String(row.destination ?? row.target ?? ''),
        payloadHash: String(row.payload_hash ?? row.payloadHash ?? ''),
        payloadPreview:
          (row.payload_preview as Record<string, unknown>) ??
          (row.payload as Record<string, unknown>) ??
          {},
        expiresAt: String(row.expires_at ?? row.expiresAt ?? ''),
        revokedAt: (row.revoked_at as string | null) ?? (row.revokedAt as string | null) ?? null,
      })
    }
  }

  const history = historyFromList(items).map((h) =>
    h.missionId === mission.missionId
      ? { ...h, artifactCount: Math.max(h.artifactCount, artifacts.length) }
      : h,
  )

  mission = {
    ...mission,
    busyWorkers: workers.filter((w) => w.status === 'busy' || w.claimed).length,
    logicalAgents: workers.length,
  }

  const liveErrors: string[] = []
  if (!goalsRes.ok) {
    liveErrors.push(`Goals API unavailable (HTTP ${goalsRes.status}) — mission UI still loads.`)
  }
  if (!items.length && !goals.length) {
    liveErrors.push('No durable goals or missions yet (honest empty live state).')
  } else if (!items.length) {
    liveErrors.push('No durable missions in MissionStore yet (honest empty live state).')
  }

  return emptyLiveSnapshot({
    mission,
    history,
    routes,
    workers,
    projects,
    artifacts,
    events,
    approvals,
    goals,
    selectedGoalId,
    serverReady,
    capacity: ((capacity.buckets ?? []) as Array<{
      bucket_id: string
      dimension: string
      remaining: number | null
      limit: number | null
    }>).map((b) => ({
      bucketId: b.bucket_id,
      dimension: b.dimension,
      remaining: b.remaining,
      limit: b.limit,
    })),
    errors: liveErrors,
    mockVsLive:
      String(capacity.mock_vs_live ?? '') ||
      'live_goals_missions_artifacts_workers_projects_from_api_not_fixtures',
  })
}

export type ConsoleRuntimeConfig = {
  mode?: 'mock' | 'live'
  baseUrl?: string
  token?: string
  sameOrigin?: boolean
}

declare global {
  interface Window {
    __SWARM_CONSOLE__?: ConsoleRuntimeConfig
  }
}

/**
 * Resolve console mode from query string + optional product-compose runtime-config.js.
 * Default is live/operational empty — mock fixtures require explicit ?mode=mock.
 * Product compose sets sameOrigin so baseUrl defaults to window.location.origin (nginx proxy).
 */
export function resolveConsoleLoadOpts(): {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
  missionId?: string
  goalId?: string
} {
  if (typeof window === 'undefined') {
    return { mode: 'live' }
  }
  const cfg = window.__SWARM_CONSOLE__ ?? {}
  const params = new URLSearchParams(window.location.search)
  const mode: 'mock' | 'live' =
    params.get('mode') === 'mock'
      ? 'mock'
      : params.get('mode') === 'live'
        ? 'live'
        : cfg.mode === 'mock'
          ? 'mock'
          : 'live'
  const sameOrigin = cfg.sameOrigin === true
  const baseUrl =
    params.get('baseUrl') ||
    cfg.baseUrl ||
    (sameOrigin ? window.location.origin : undefined) ||
    undefined
  const token = params.get('token') || cfg.token || undefined
  const missionId = params.get('missionId') || undefined
  const goalId = params.get('goalId') || undefined
  return { mode, baseUrl, token, missionId, goalId }
}

/** Live: POST /v1/workers/cancel-lease */
export async function cancelLiveWorkerLease(opts: {
  baseUrl: string
  token?: string
  leaseId: string
  reason?: string
}): Promise<{ lease_id: string; state: string; reason?: string | null }> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  const payload = await mutateJson(`${base}/v1/workers/cancel-lease`, headers, 'POST', {
    lease_id: opts.leaseId,
    reason: opts.reason ?? 'operator_cancel',
  })
  return {
    lease_id: String(payload.lease_id ?? opts.leaseId),
    state: String(payload.state ?? 'cancelled'),
    reason: (payload.reason as string | null | undefined) ?? null,
  }
}

/** Live: POST /v1/approvals/{id}/resolve */
export async function resolveLiveApproval(opts: {
  baseUrl: string
  token?: string
  approvalId: string
  accept: boolean
  payload?: Record<string, unknown>
}): Promise<Record<string, unknown>> {
  const headers: Record<string, string> = {}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const base = opts.baseUrl.replace(/\/$/, '')
  return mutateJson(
    `${base}/v1/approvals/${encodeURIComponent(opts.approvalId)}/resolve`,
    headers,
    'POST',
    { accept: opts.accept, payload: opts.payload ?? null },
  )
}

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
