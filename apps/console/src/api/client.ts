/** Browser API client — never embeds provider secrets. */

import type { ConsoleSnapshot, HistoryRow, MissionGraph } from './types'
import { MOCK_SNAPSHOT } from '../data/fixtures'

const SECRET_RE = /(sk-[a-zA-Z0-9]+|api_key\s*=\s*\S+)/i

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
  errors?: string[]
  mockVsLive?: string
}): ConsoleSnapshot {
  return {
    mode: 'live',
    mockVsLive:
      opts?.mockVsLive ??
      'operational_empty_or_observed_from_api_not_fixture_catalog',
    mission: opts?.mission ?? emptyLiveMission(),
    routes: opts?.routes ?? [],
    capacity: opts?.capacity ?? [],
    capacityUnknown: !(opts?.capacity && opts.capacity.length),
    workers: opts?.workers ?? [],
    profiles: [],
    approvals: [],
    projects: [],
    history: opts?.history ?? [],
    artifacts: [],
    events: [],
    streamInterrupted: false,
    errors: opts?.errors ?? [],
  }
}

function missionFromApi(raw: Record<string, unknown>): MissionGraph {
  return {
    missionId: String(raw.id ?? raw.mission_id ?? '(unknown)'),
    revision: Number(raw.revision ?? 1),
    status: String(raw.status ?? 'unknown'),
    objective: String(raw.objective ?? raw.goal ?? ''),
    tasks: [],
    planningRoles: [],
    logicalAgents: 0,
    busyWorkers: 0,
    inFlightInference: 0,
  }
}

function historyFromList(items: Array<Record<string, unknown>>): HistoryRow[] {
  return items.map((row) => ({
    missionId: String(row.mission_id ?? ''),
    projectId: (row.project_id as string | null) ?? null,
    goal: String(row.objective ?? row.goal ?? ''),
    status: String(row.status ?? 'unknown'),
    costUsd: 0,
    artifactCount: 0,
    tags: [String(row.source ?? 'mission_store')],
    updatedAt: String(row.updated_at ?? ''),
  }))
}

export async function createLiveMission(opts: {
  baseUrl: string
  token?: string
  objective: string
  projectId: string
  taskFamily?: string
  requiredChecks?: Record<string, boolean>
  hiddenAcceptance?: Record<string, unknown>
}): Promise<MissionGraph> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const body: Record<string, unknown> = {
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
  if (opts.taskFamily) body.task_family = opts.taskFamily
  if (opts.requiredChecks) body.required_checks = opts.requiredChecks
  if (opts.hiddenAcceptance) body.hidden_acceptance = opts.hiddenAcceptance
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

export async function executeLiveMission(opts: {
  baseUrl: string
  token?: string
  missionId: string
  model?: string
}): Promise<Record<string, unknown>> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`
  const res = await fetch(`${opts.baseUrl}/v1/missions/${opts.missionId}/execute`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ model: opts.model ?? 'gemma3:4b' }),
  })
  if (!res.ok) {
    throw new Error(`api_error_${res.status}`)
  }
  const payload = (await res.json()) as Record<string, unknown>
  assertNoSecretsInBundle(payload)
  return payload
}

export async function loadSnapshot(opts: {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
}): Promise<ConsoleSnapshot> {
  // Fixture UI is explicit mock mode only — never mixed into live/operational.
  if (opts.mode === 'mock') {
    const snap = structuredClone(MOCK_SNAPSHOT)
    assertNoSecretsInBundle(snap)
    return snap
  }

  if (!opts.baseUrl) {
    // Live/operational without an API base: honest empty, not fixtures.
    const snap = emptyLiveSnapshot({
      errors: [
        'Live mode with no baseUrl — showing empty operational state (not mock fixtures).',
      ],
      mockVsLive: 'operational_empty_no_api_base_not_fixture_catalog',
    })
    assertNoSecretsInBundle(snap)
    return snap
  }

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`

  const [capacityRes, missionsRes, routesRes, workersRes] = await Promise.all([
    fetch(`${opts.baseUrl}/v1/capacity`, { headers }),
    fetch(`${opts.baseUrl}/v1/missions`, { headers }),
    fetch(`${opts.baseUrl}/v1/routes`, { headers }),
    fetch(`${opts.baseUrl}/v1/workers`, { headers }),
  ])
  if (!capacityRes.ok) {
    throw new Error(`api_error_${capacityRes.status}`)
  }
  if (!missionsRes.ok) {
    throw new Error(`api_error_${missionsRes.status}`)
  }
  const capacity = await capacityRes.json()
  const missionsPayload = await missionsRes.json()
  assertNoSecretsInBundle(capacity)
  assertNoSecretsInBundle(missionsPayload)

  const items = Array.isArray(missionsPayload.missions)
    ? (missionsPayload.missions as Array<Record<string, unknown>>)
    : Array.isArray(missionsPayload.items)
      ? (missionsPayload.items as Array<Record<string, unknown>>)
      : []
  let mission = emptyLiveMission()
  if (items.length > 0) {
    const firstId = String(items[0].mission_id ?? '')
    if (firstId) {
      const detailRes = await fetch(`${opts.baseUrl}/v1/missions/${firstId}`, { headers })
      if (detailRes.ok) {
        const detail = await detailRes.json()
        assertNoSecretsInBundle(detail)
        mission = missionFromApi((detail.mission ?? items[0]) as Record<string, unknown>)
      } else {
        mission = missionFromApi(items[0])
      }
    }
  }

  const routes: ConsoleSnapshot['routes'] = []
  if (routesRes.ok) {
    const routesPayload = await routesRes.json()
    assertNoSecretsInBundle(routesPayload)
    for (const row of (routesPayload.routes ?? []) as Array<Record<string, unknown>>) {
      routes.push({
        routeId: String(row.route_id ?? row.routeId ?? ''),
        provider: String(row.provider ?? row.provider_id ?? 'unknown'),
        modelId: (row.model_id as string | null) ?? null,
        availability: String(row.availability_status ?? row.availability ?? 'unknown') as ConsoleSnapshot['routes'][0]['availability'],
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
    const workersPayload = await workersRes.json()
    assertNoSecretsInBundle(workersPayload)
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

  return emptyLiveSnapshot({
    mission,
    history: historyFromList(items),
    routes,
    workers,
    capacity: (capacity.buckets ?? []).map(
      (b: {
        bucket_id: string
        dimension: string
        remaining: number | null
        limit: number | null
      }) => ({
        bucketId: b.bucket_id,
        dimension: b.dimension,
        remaining: b.remaining,
        limit: b.limit,
      }),
    ),
    errors: items.length
      ? []
      : ['No durable missions in MissionStore yet (honest empty live state).'],
    mockVsLive:
      String(capacity.mock_vs_live ?? '') ||
      'live_missions_capacity_routes_workers_from_api_not_fixtures',
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
} {
  if (typeof window === 'undefined') {
    return { mode: 'live' }
  }
  const params = new URLSearchParams(window.location.search)
  const mode = params.get('mode') === 'mock' ? 'mock' : 'live'
  const baseUrl = params.get('baseUrl') || undefined
  const token = params.get('token') || undefined
  return { mode, baseUrl, token }
}
