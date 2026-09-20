/** Shared API/console types — aligned with SwarmAI /v1 contracts. */

export type Availability =
  | 'available'
  | 'unknown'
  | 'retired'
  | 'disabled'
  | 'gated'
  | 'exhausted'

export type ProfileState = 'provisional' | 'qualified' | 'stale' | 'quarantine' | 'unknown'

export interface MissionTask {
  id: string
  objective: string
  status: string
  roleHint?: string
  waitingReason?: string
  unblockEvent?: string
}

export interface MissionGraph {
  missionId: string
  revision: number
  status: string
  objective: string
  tasks: MissionTask[]
  planningRoles: string[]
  logicalAgents: number
  busyWorkers: number
  inFlightInference: number
}

export interface RouteRow {
  routeId: string
  provider: string
  modelId: string | null
  availability: Availability
  status: string
  capabilityClaims: string[]
}

export interface CapacityBucket {
  bucketId: string
  dimension: string
  remaining: number | null
  limit: number | null
  note?: string
}

export interface WorkerRow {
  workerId: string
  status: string
  generation: number
  capacity: number
  privacy: string[]
  claimed: string | null
  revoked: boolean
  stale?: boolean
}

export interface ProfileRow {
  key: string
  taskFamily: string
  sizeBand: string
  state: ProfileState
  wilsonLower?: number
  distinctCases?: number
}

export interface ApprovalRow {
  id: string
  operation: string
  destination: string
  payloadHash: string
  payloadPreview: Record<string, unknown>
  expiresAt: string
  revokedAt: string | null
}

export interface ConsoleSnapshot {
  mode: 'mock' | 'live'
  mockVsLive: string
  mission: MissionGraph
  routes: RouteRow[]
  capacity: CapacityBucket[]
  capacityUnknown: boolean
  workers: WorkerRow[]
  profiles: ProfileRow[]
  approvals: ApprovalRow[]
  events: { id: string; type: string; summary: string }[]
  streamInterrupted: boolean
  errors: string[]
}
