/** Browser API client — never embeds provider secrets. */

import type { ConsoleSnapshot, HistoryRow, MissionGraph, MissionTask } from './types'
import { MOCK_SNAPSHOT } from '../data/fixtures'

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
    routes: opts?.routes ?? [],
    capacity: opts?.capacity ?? [],
    capacityUnknown: !(opts?.capacity && opts.capacity.length),
    workers: opts?.workers ?? [],
    profiles: [],
    approvals: [],
    projects: opts?.projects ?? [],
    history: opts?.history ?? [],
    artifacts: opts?.artifacts ?? [],
    events: opts?.events ?? [],
    streamInterrupted: false,
    errors: opts?.errors ?? [],
  }
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
}): Promise<ConsoleSnapshot> {
  // Fixture UI is explicit mock mode only — never mixed into live/operational.
  if (opts.mode === 'mock') {
    const snap = structuredClone(MOCK_SNAPSHOT)
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

  const [readyRes, capacityRes, missionsRes, routesRes, workersRes, projectsRes] =
    await Promise.all([
      fetchJson(`${base}/health/ready`, headers),
      fetchJson(`${base}/v1/capacity`, headers),
      fetchJson(`${base}/v1/missions`, headers),
      fetchJson(`${base}/v1/routes`, headers),
      fetchJson(`${base}/v1/workers`, headers),
      fetchJson(`${base}/v1/projects`, headers),
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

  const items = Array.isArray(missionsPayload.missions)
    ? (missionsPayload.missions as Array<Record<string, unknown>>)
    : Array.isArray(missionsPayload.items)
      ? (missionsPayload.items as Array<Record<string, unknown>>)
      : []

  const preferredId = (opts.missionId || '').trim()
  const selectedRow =
    (preferredId && items.find((row) => String(row.mission_id ?? '') === preferredId)) ||
    items[0] ||
    null

  let mission = emptyLiveMission()
  let artifacts: ConsoleSnapshot['artifacts'] = []
  let events: ConsoleSnapshot['events'] = []

  if (selectedRow) {
    const missionId = String(selectedRow.mission_id ?? '')
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
      workers.push({
        workerId: String(row.worker_id ?? row.workerId ?? ''),
        status: String(row.status ?? 'unknown'),
        generation: Number(row.generation ?? 0),
        capacity: Number(row.capacity ?? 0),
        privacy: Array.isArray(row.privacy) ? (row.privacy as string[]) : [],
        claimed: (row.claimed as string | null) ?? null,
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

  return emptyLiveSnapshot({
    mission,
    history,
    routes,
    workers,
    projects,
    artifacts,
    events,
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
    errors: items.length
      ? []
      : ['No durable missions in MissionStore yet (honest empty live state).'],
    mockVsLive:
      String(capacity.mock_vs_live ?? '') ||
      'live_missions_artifacts_workers_projects_from_api_not_fixtures',
  })
}

/**
 * Resolve console mode from query string.
 * Default is live/operational empty — mock fixtures require explicit ?mode=mock.
 */
export function resolveConsoleLoadOpts(): {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
  missionId?: string
} {
  if (typeof window === 'undefined') {
    return { mode: 'live' }
  }
  const params = new URLSearchParams(window.location.search)
  const mode = params.get('mode') === 'mock' ? 'mock' : 'live'
  const baseUrl = params.get('baseUrl') || undefined
  const token = params.get('token') || undefined
  const missionId = params.get('missionId') || undefined
  return { mode, baseUrl, token, missionId }
}
