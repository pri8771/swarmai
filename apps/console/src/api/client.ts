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
}): Promise<ConsoleSnapshot> {
  if (opts.mode === 'mock' || !opts.baseUrl) {
    const snap = structuredClone(MOCK_SNAPSHOT)
    assertNoSecretsInBundle(snap)
    return snap
  }
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`

  const [capacityRes, missionsRes] = await Promise.all([
    fetch(`${opts.baseUrl}/v1/capacity`, { headers }),
    fetch(`${opts.baseUrl}/v1/missions`, { headers }),
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

  return {
    ...MOCK_SNAPSHOT,
    mode: 'live',
    mockVsLive:
      'live_missions_and_capacity_from_api; routes/workers/profiles still fixture-labeled until wired',
    mission,
    history: historyFromList(items),
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
    capacityUnknown: !(capacity.buckets && capacity.buckets.length),
    errors: items.length
      ? []
      : ['No durable missions in MissionStore yet (honest empty live state).'],
    events: [],
  }
}

/** Resolve console mode from query string (?mode=live&baseUrl=...). */
export function resolveConsoleLoadOpts(): {
  mode: 'mock' | 'live'
  baseUrl?: string
  token?: string
} {
  if (typeof window === 'undefined') {
    return { mode: 'mock' }
  }
  const params = new URLSearchParams(window.location.search)
  const mode = params.get('mode') === 'live' ? 'live' : 'mock'
  const baseUrl = params.get('baseUrl') || undefined
  const token = params.get('token') || undefined
  return { mode, baseUrl, token }
}
