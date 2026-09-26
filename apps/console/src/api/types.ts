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
  /** Active dispatch lease IDs (for operator cancel-lease). */
  activeLeases: string[]
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

/** Goal entity — aligned with /v1/goals (Lane C V1.8) + pursuit (Lane D V1.9). */
export type GoalStatus =
  | 'active'
  | 'waiting'
  | 'blocked'
  | 'paused'
  | 'achieved'
  | 'cancelled'
  | 'expired'

export type GoalKind = 'finite' | 'ongoing'

export interface GoalDecision {
  at: string
  actor: string
  from?: string
  to?: string
  action?: string
  reason?: string
  [key: string]: unknown
}

export interface GoalProgressEntry {
  at: string
  actor: string
  summary: string
  metrics?: Record<string, unknown>
}

export interface GoalMissionOutcome {
  at: string
  mission_id: string
  outcome: string
  actor: string
  notes?: string
  evidence_refs?: string[]
}

export interface PursuitCycle {
  cycle_id?: string
  goal_id?: string
  phase?: string
  decided_kind?: string | null
  notes?: string
  strategy_after?: string | null
  at?: string
  [key: string]: unknown
}

export interface PursuitStatus {
  goal_id: string
  schedule?: Record<string, unknown>
  history: PursuitCycle[]
  commitments: string[]
  adopted_lessons: Array<Record<string, unknown>>
}

export interface GoalRow {
  id: string
  projectId: string
  desiredOutcome: string
  verificationCriteria: string[]
  kind: GoalKind
  scope: Record<string, unknown>
  constraints: Record<string, unknown>
  resourceEnvelope: Record<string, unknown>
  authorityEnvelope: Record<string, unknown>
  owner: string
  permittedAgents: string[]
  strategy: string
  evidenceRefs: string[]
  missionIds: string[]
  dependencies: string[]
  missionOutcomes: GoalMissionOutcome[]
  openQuestions: string[]
  blockers: string[]
  stopConditions: string[]
  reviewCadence: string | null
  expiresAt: string | null
  status: GoalStatus
  progress: GoalProgressEntry[]
  decisionHistory: GoalDecision[]
  triggerReceipts: Array<Record<string, unknown>>
  restartCount: number
  createdAt: string
  updatedAt: string
  pursuit?: PursuitStatus | null
}

export interface ConsoleSnapshot {
  mode: 'mock' | 'live'
  mockVsLive: string
  hostnamePublic: string
  serverReady: boolean | null
  mission: MissionGraph
  goals: GoalRow[]
  selectedGoalId: string | null
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
