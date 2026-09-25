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

export interface ProjectRow {
  projectId: string
  name: string
  repoPath: string
  allowPaid: boolean
  allowedTools: string[]
  updatedAt: string
}

export interface HistoryRow {
  missionId: string
  projectId: string | null
  goal: string
  status: string
  costUsd: number
  artifactCount: number
  tags: string[]
  updatedAt: string
}

export interface ArtifactRow {
  artifactId: string
  kind: string
  uri?: string
  summary?: string
  contentHash?: string
  mediaType?: string
  byteLength?: number
}

export interface ConsoleSnapshot {
  mode: 'mock' | 'live'
  mockVsLive: string
  hostnamePublic: string
  serverReady: boolean | null
  mission: MissionGraph
  routes: RouteRow[]
  capacity: CapacityBucket[]
  capacityUnknown: boolean
  workers: WorkerRow[]
  profiles: ProfileRow[]
  approvals: ApprovalRow[]
  projects: ProjectRow[]
  history: HistoryRow[]
  artifacts: ArtifactRow[]
  events: { id: string; type: string; summary: string }[]
  streamInterrupted: boolean
  errors: string[]
}
